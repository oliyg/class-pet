# pynput / apscheduler / tendo 机制与实测记录

本页是 `AGENTS.md` 里 worker 与单实例规则的**依据**。三者共同点：回调或任务都不跑在 GUI 线程上。

## pynput：全局钩子

- 回调跑在 pynput 自己的**钩子线程**（守护线程）上，实测回调里 `threading.current_thread().name` 不是 `MainThread`——所以回调里绝不能碰控件，`InputMonitor.activity` 只 `emit`，由 Qt 排队回 GUI 线程。
- **回调的返回值会被当停表信号**：返回 `False` 时抛 `StopException` 终止监听，所以回调一律返回 `None`。
- **参数个数会被自动适配**：`keyboard.Listener` 用 `_wrap(on_press, 2)`、`mouse.Listener` 用 `_wrap(on_click, 5)`（`on_scroll` 5 个、`on_move` 3 个）。少写参数会被截断（`on_move(x, y)` 收不到第三个 `injected`），多写在构造时抛 `ValueError`。**别为消 basedpyright 的 `reportUnusedParameter` 删参数**，那会让后面的参数错位。
- **`stop()` 不能在钩子线程内调用**：本项目在 `app.aboutToQuit` 里摘下钩子。
- **跨线程计数不能用 `+= 1`**：键盘与鼠标钩子分属两个线程，用 `itertools.count()` 的 `next()`（原子操作）。
- **`time.monotonic()` 在 Windows 上是 `GetTickCount64`，粒度 15.625 ms**：同一 tick 内连续两次读取会相等，空闲时长不要假设更高精度（控制台显示"空闲：0 秒"就是这么来的）。
- **不要读 `key.char`**：全局记录按键内容等同于键盘记录器，只在确实需要全局快捷键时读具体键。

## apscheduler：定时任务

- **`QtScheduler` 的唤醒走 Qt 事件循环**（内部就是 `QTimer.singleShot(ms, self._process_jobs)` + 重排下一次），不额外起调度线程；`BackgroundScheduler` 自带调度线程，在 Qt 应用里没有意义。
- **但任务体不跑在 GUI 线程**：`QtScheduler` 只管"何时唤醒"，任务仍交给默认 `ThreadPoolExecutor`——实测任务里 `threading.current_thread().name` 是 `ThreadPoolExecutor-0_0`。任务里只能 `emit` 信号。真要同步跑可以换 executor，代价是一次慢任务就冻住界面。
- **生命周期挂在入口**：`SchedulerWorker` 是 `QObject`，但内部的 `QtScheduler` 不是、挂不了父对象，别指望窗口析构替你收尾；入口 `scheduler.start()` + `app.aboutToQuit.connect(scheduler.shutdown)`，`shutdown(wait=False)` 是不让卡住的任务拖住进程退出。
- `start()` 之前 `add_job` 也可以：任务先进 `_pending_jobs`，`start()` 时统一入库。
- 状态机：重复 `start()` 抛 `SchedulerAlreadyRunningError`（我们的 `start()` 直接透传）。apscheduler 的裸 `shutdown()` 在未启动时会抛 `SchedulerNotRunningError`，但**我们的包装先判 `running`**，所以 `SchedulerWorker.shutdown()` 可以安全重复调用——退出路径（`aboutToQuit`）不一定经历过启动路径。
- 默认 jobstore 是 `MemoryJobStore`，重启不保留，任务靠代码重新注册。
- **不要升 4.x**：4.x 是重写过的 async API、`add_job` 那一套会变，且目前只有预发布版——实测 `uv run --with "apscheduler>=4"` 报 `only apscheduler<=4.0.0a6 is available`。uv 解析到 3.11.3 是正确的。
- 界面刷新不要用它：控制台每秒刷空闲时长用的是 `QTimer`，换调度器只会把纯界面更新变成每秒一次跨线程信号往返。

## tendo：单实例

- **`SingleInstance` 必须持引用**：实测不持引用时第二个实例照常启动——对象一被回收，`__del__` 就关句柄、删锁文件。`main()` 里那行带 `# noqa: F841` 的赋值是承重的，不要"清理"，也不要用 `--unsafe-fixes`。
- **锁文件**：`%TEMP%\<sys.argv[0] 绝对路径转义>-main-<flavor_id>.lock`，开发态是 `%TEMP%\C-Users-...-class-pet-run_classpet-class-pet.lock`。名字依赖脚本路径，所以换目录启动视为不同实例（打包版与开发版因此可同时运行）。
- **Windows 上的判定机制**：`os.unlink` 现有锁文件 → 运行中的实例持有该文件，删除会失败并抛 `PermissionError`（`WinError 32`，errno 13）→ `tendo` 据此抛 `SingleInstanceException`。它不是端口/互斥体方案，全靠"文件被占用则删不掉"。
- **`SingleInstanceException` 继承 `BaseException`**：`except Exception` 抓不到，必须显式捕获；不捕获会打印一大段（含中文本地化 WinError 文案的）traceback 并返回 1。
- **异常退出会遗留锁文件**（被强杀时 `__del__` 不执行），下次启动会先 `unlink` 陈旧锁再创建，能自愈；正常退出由 `__del__` 清理干净。
- 单实例检查在 `main()` 开头、`QApplication` 之前，但**模块级 import 已经发生**：第二个实例仍会跑完全部 import（含 qfluentwidgets 横幅）才退出。
- 第二个实例的提示由 `report_already_running()` 按环境分流：`getattr(sys, "frozen", False)` 为真（打包后无控制台）弹 `QMessageBox`——**它阻塞等用户点确定**，所以第二个实例会停在进程列表里；开发态写 stderr。
- 要做"唤出已有窗口"需要另加 IPC（`QLocalServer` / `QSharedMemory`），`tendo` 不提供。
