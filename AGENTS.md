# AGENTS.md

## 项目概览

`class-pet`（课小宠 ClassPet）：面向教师的桌面助手，目标形态是课表 / 调课 / 上课通知。PySide6 桌面端应用，UI 层用 **qfluentwidgets**。入口为 `run_classpet.py`（只做编排），业务代码在 `classpet/` 包里。当前是 `FluentWindow` + 左侧导航（控制台 / 设置）+ 全局输入监听 + 定时提醒 + 开机自启动的骨架，业务功能尚未实现。

## 环境与命令

系统 PATH 上**没有 `python`**，`python` / `python3` 均指向 Microsoft Store 别名并报错。所有命令必须走 `uv`：

```bash
uv sync                   # 同步依赖
uv run run_classpet.py    # 运行应用
uv run python -c ...      # 执行临时脚本
uv run ruff check .       # 静态检查
uv run basedpyright       # 类型检查
uv run pyinstaller --noconfirm class-pet.spec  # 打包（先关掉正在运行的 exe）
```

- 已安装：PySide6 6.11.2（`pyside6` + `pyside6-essentials` + `pyside6-addons` + `shiboken6`）
- 已安装 UI 库：qfluentwidgets 1.11.3（PyPI 包名 `pyside6-fluent-widgets`），随之带入 `pysidesix-frameless-window`、`darkdetect`、`pywin32`。
- 已安装输入监听：pynput 1.8.2（随附 `six`）。
- 已安装单实例：tendo 0.3.0。
- 已安装定时任务：apscheduler 3.11.3（3.x API，随附 `tzdata`、`tzlocal`）。
- 开发依赖（`[dependency-groups] dev`）：ruff 0.16.8、basedpyright 1.40.1、pyinstaller 6.22.3、pillow 12.3.0。
- `pyproject.toml` 中 `package = false`：本项目是可执行的脚本目录，不是可安装包，新增模块时无需构建后端。

## 结构约束

- 目录按职责分层（参照同类桌面宠物项目 DyberPet 的组织方式），不要退化回单文件：
  - `run_classpet.py` 只做编排：创建对象、连接跨模块信号、启停、进入事件循环。
  - `classpet/modules.py` 放后台 worker（只发信号，不碰控件）、`classpet/notification.py` 放通知、`classpet/dashboard/` 放界面与页面、`classpet/utils.py` 放通用工具。
  - `res/` 放运行时资源，按类型分子目录（现在只有 `res/icons/`）。
  - 平台相关功能放自己的子包（如 `classpet/self_startup/`：门面 + `win32.py`），门面按 `sys.platform` 分发；**没有实现的平台不要写空实现或占位文件**。
- **模块之间不互相 import**：worker 与界面靠 Signal 连接，连线统一写在 `run_classpet.py`。界面需要外部模块时用 `MainWindow.setup_*` 这类钩子，不要让界面自己去 new 后台对象。
- 入口保持 `main() -> int` + `if __name__ == "__main__": sys.exit(main())` 的形式（写在 `run_classpet.py`）。
- 不要引入未被要求的依赖、配置、脚手架、空目录或占位文件；还没有内容的分层（如 `settings.py`、`conf.py`）就先不建。
- 机制类说明写进 `docs/`（现有 `docs/hkcu.md`）：它讲的是"某个系统机制是什么、我们为什么这么用"。README 只留使用者需要的内容，别把它撑成技术手册。新增 docs 时同步补 README 的目录树。

## 代码约定

- 缩进 4 空格，双引号。命名：函数、变量、模块名用 `snake_case`，类名用 `PascalCase`，私有成员加单个下划线前缀。
- Qt 导入一律用 `PySide6.*`，不要用 `PyQt*` 或 `PySide2`。
- UI 控件优先用 `qfluentwidgets`（`FluentWindow`、`PushButton`、`BodyLabel`、`SubtitleLabel` 等）；`PySide6.QtWidgets` 只用来搭布局与容器（`QWidget`、`QVBoxLayout`）。同一控件两套写法混用属于禁止项。
  - **有意偏离（不算违规，但不要扩大）**：托盘相关只能用原生 `QSystemTrayIcon` / `QMenu`——qfluentwidgets 没有托盘实现，它的 `RoundMenu` 是窗口内菜单；启动早期与失败路径用原生 `QMessageBox`——它不依赖 qfluentwidgets 的初始化状态。除这两类，新增界面一律用 qfluentwidgets。
- 未配置测试框架与 formatter（无 pytest / black）。已引入 ruff 做静态检查（`uv run ruff check .`），不要换别的 linter，也不要擅自加规则。
- 类型检查用 basedpyright（`uv run basedpyright`），配置在 `pyproject.toml` 的 `[tool.basedpyright]`。**不要顺手把它调成 `recommended`**，理由见下。
- **禁止 `ruff check --fix --unsafe-fixes`**：其中「移除未使用的 `instance`」会静默破坏单实例（见下）。

## basedpyright 注意点

- **严格度定在 `standard`，不是它的默认档 `recommended`。** 实测同一份代码：`recommended` = `0 error / 68 warning`，`standard` = `0 / 0`。68 条里 44 条是 `Unknown` 家族连锁，根因是 **qfluentwidgets 与 pynput 都没有类型信息**（无 `py.typed`、无 `.pyi`；PySide6 有 60 个 `.pyi`、tendo 有 `py.typed`），另有 10 条 `reportUnusedParameter`（pynput 回调参数）、8 条 `reportUnannotatedClassAttribute`、4 条 `reportUnusedCallResult`、1 条 `reportUnusedVariable`。改成 `recommended` 只会得到一墙黄色波浪线，不会挡住真问题。
- 想收紧的**正确顺序**：先给 `classpet/` 里的代码补类型注解 → 再升档。届时注意两点：
  - 那个承重的 `instance` 会以 `reportUnusedVariable` 出现，而 **basedpyright 不认 `# noqa: F841`**，要用 `# pyright: ignore[reportUnusedVariable]`；ruff 与 basedpyright 是两套抑制语法，别只加一边。
  - pynput 回调参数**不能**为了消警告删掉：`_wrap` 取前 N 个参数，删掉 `x, y` 会让 `pressed` 错位接到 `x`（详见 pynput 节）。
- `include` / `exclude` **一旦写了就是替换，不是追加**：`include` 覆盖 pyright 默认的根目录扫描（所以 `**/*.py` 与 `class-pet.spec` 必须显式列出），`exclude` 覆盖默认的 `node_modules` / `__pycache__` / 点开头目录（所以要把这三项连同 `build`、`dist` 一起列全）。
- **`class-pet.spec` 在 include 里，这是故意的**：它就是靠 `reportUndefinedVariable` 拦住"删掉 spec 顶部 import"这类改动的。实测删掉那两行 → `rc=1` + 4 条 `reportUndefinedVariable`（`Analysis` / `PYZ` / `EXE` / `COLLECT`）；补回 → `rc=0`。
- Zed 自带一份同版本（`%LOCALAPPDATA%\Zed\languages\basedpyright`，Zed 与 `ruff` 都放那儿），所以编辑器里看到的诊断来自 Zed 那份；项目这份由 `uv.lock` 固定，供 CI 与命令行使用。两者版本目前一致（1.40.1）。
- 只想卡错误时用 `uv run basedpyright --level error`（`--level` 取 `error` 或 `warning`）。

## qfluentwidgets 注意点

- `addSubInterface(interface, ...)` 要求 `interface.objectName()` 非空，否则抛 `ValueError`。新增页面时先 `setObjectName(...)`。
- `QApplication.setHighDpiScaleFactorRoundingPolicy(...)` 必须在构造 `QApplication` **之前**调用。
- 1.11.3 的控件构造函数只接 `parent`，文本用 `setText()` 赋值（不要照抄旧版文档里 `PushButton("确定", self)` 的写法）。
- `import qfluentwidgets` 会向 stdout 打印一行 Pro 版推广横幅，属上游行为，不要试图屏蔽。

## pynput 注意点

- **线程**：回调跑在 pynput 自己的钩子线程上，绝不能直接操作控件。必须经 `Signal` 发出，由 Qt 排队回 GUI 线程（`InputMonitor.activity` 就是这么做的）。
- **回调返回 `False` 会终止监听**：pynput 把 `False` 当停表信号抛 `StopException`。回调一律返回 `None`。
- **参数个数会被自动适配**：`keyboard.Listener` 用 `_wrap(on_press, 2)`、`mouse.Listener` 用 `_wrap(on_click, 5)`。回调少写参数会被截断（`on_move(x, y)` 收不到第三个 `injected`），多写则在构造时抛 `ValueError`。
- **必须成对启停**：`start()` 后要在 `app.aboutToQuit` 里 `stop()` 摘钩子；`stop()` 不能在钩子线程内调用。钩子线程本身是守护线程。
- **跨线程计数不能用 `+= 1`**：键盘与鼠标钩子在两个线程上，用 `itertools.count()` 的 `next()`（原子）代替。
- **`time.monotonic()` 在 Windows 上是 `GetTickCount64`，粒度 15.625 ms**：同一 tick 内连续两次读取会相等，空闲判断不要假设更高精度。
- **默认不读 `key.char`**：全局记录按键内容等同于键盘记录器。只在确实需要全局快捷键时读具体键。

## tendo 单实例注意点

- **必须持有 `SingleInstance` 实例的引用**（`main()` 里的 `instance` 是承重的，不是废变量）。对象一旦被回收，`__del__` 会立刻关掉句柄并删掉锁文件，单实例随即失效——实测不持引用时第二个实例照常启动。
- 因此该行带 `# noqa: F841`：ruff 会报"赋值后未使用"，那是**故意抑制**，不要"清理"它，也别用 `--unsafe-fixes`。
- **锁文件路径**：`%TEMP%\<sys.argv[0] 绝对路径转义>-main-<flavor_id>.lock`，本项目的例子是 `%TEMP%\C-Users-...-class-pet-main-class-pet.lock`。名字依赖脚本路径，所以换目录启动视为不同实例。
- **Windows 上的判定机制**：`os.unlink` 现有锁文件 → 运行中的实例持有该文件，删除会失败并抛 `PermissionError`（`WinError 32`，errno 13）→ `tendo` 据此抛 `SingleInstanceException`。它不是端口/互斥体方案，全靠"文件被占用则删不掉"。
- **`SingleInstanceException` 继承自 `BaseException`**，`except Exception` 抓不到，必须显式捕获。不捕获会打印一大段（含中文本地化 WinError 文案的）traceback 并返回 1。
- **异常退出会遗留锁文件**（被强杀时 `__del__` 不执行，实测残留），但下次启动会先 `unlink` 陈旧锁再创建，能自愈。正常退出由 `__del__` 清理干净。
- 单实例检查放在 `main()` 开头、`QApplication` 之前，但**模块级 import 已经发生**：第二个实例仍会执行全部 import 并打印 qfluentwidgets 横幅，然后才退出。
- 第二个实例的提示由 `report_already_running()` 按环境分流：`getattr(sys, "frozen", False)` 为真（打包后没有控制台）就弹 `QMessageBox`，否则写 stderr。若要做"唤出已有窗口"，需要另加 IPC（`QLocalServer`/`QSharedMemory`），`tendo` 不提供。

## apscheduler 注意点

- **用 `QtScheduler`（`apscheduler.schedulers.qt`），不要换成 `BackgroundScheduler`。** 前者的唤醒走 Qt 事件循环（内部就是 `QTimer.singleShot(ms, self._process_jobs)` + 重排下一次），不额外起调度线程；`BackgroundScheduler` 会自带一个调度线程，在 Qt 应用里没有意义。
- **但任务体不跑在 GUI 线程。** `QtScheduler` 只接管"何时唤醒"，任务仍交给默认的 `ThreadPoolExecutor` 执行——实测任务里 `threading.current_thread().name` 是 `ThreadPoolExecutor-0_0`，而 GUI 是 `MainThread`。所以任务函数里**不能直接操作控件**，必须经 `Signal` 回到 GUI 线程，与 pynput 那条规矩完全一致。若确实需要同步跑（任务极短、且要直接改 UI），可以换 executor，但那样一次慢任务就会冻住界面。
- **生命周期由 `main()` 显式负责**：入口里 `scheduler.start()` + `app.aboutToQuit.connect(scheduler.shutdown)`。`SchedulerWorker` 自己是 `QObject`，但内部的 `QtScheduler` 不是、挂不了父对象，所以别指望窗口析构能替你收尾；`wait=False` 是为了不让卡住的任务拖住进程退出。
- 状态机：`start()` 重复调用抛 `SchedulerAlreadyRunningError`；未启动就 `shutdown()` 抛 `SchedulerNotRunningError`。
- **当前只有一个测试任务** `test-reminder`（每分钟一次），注册在 `SchedulerWorker.start()`（`classpet/modules.py`）里，用途是打通「调度器 → 信号 → 系统通知」；课表/提醒规则定下来后替换掉它。加任务：`worker.scheduler.add_job(func, "interval" | "cron" | "date", ...)`；`start()` 之前 `add_job` 也可以（先进 `_pending_jobs`，`start()` 时统一入库）。默认 jobstore 是 `MemoryJobStore`，重启不保留，靠代码重新注册。
- **界面刷新不要用调度器**：控制台每秒刷新空闲时长用的是 `QTimer`（见 `classpet/dashboard/dashboard.py`）。调度器留给真正的定时任务（提醒、课表状态变化），拿它当刷新器只会把纯界面更新变成跨线程信号往返。
- **系统通知链路**：`NotificationService`（`classpet/notification.py`）持有常驻的 `QSystemTrayIcon`，`show` 是 `@Slot(str, str)`。任务体跑在 worker 线程，只 `emit` `SchedulerWorker.reminder_due`；入口把它连到 `notification.show`，跨线程自动排队回 GUI 线程。托盘图标必须 `show()` 出来，否则 `showMessage` 什么都不弹。
- 通知里显示的应用名：开发运行时是 **"Python"**，打包后是 **"class-pet.exe"**（都来自进程默认的 AppUserModelID），不是"课小宠"；要改成中文名得调 `SetCurrentProcessExplicitAppUserModelID`，目前未做。
- **不要升到 4.x**：4.x 是重写过的 async API，`add_job` 那一套会变；而且它目前只有预发布版——实测 `uv run --with "apscheduler>=4"` 报 `only apscheduler<=4.0.0a6 is available`，正式版尚未发布，所以 uv 解析到 3.11.3 是正确的。

## 开机自启动注意点

- 代码在 `classpet/self_startup/`：`__init__.py` 是门面（`is_supported` / `is_enabled` / `is_stale` / `enable` / `disable` 与 `AUTOSTART_FLAG`），`win32.py` 是 Windows 实现（`winreg` 读写 HKCU 的 Run 键）。macOS 未实现——要加就新建 `darwin.py` 并在门面的平台分发里接上，别留空文件（DyberPet 的 `SelfStartup/` 就是空壳，别重蹈）。
- **只写 `HKCU`，绝不写 `HKLM`**（后者需要管理员）。值名 `ClassPet`，值形如 `"<exe 路径>" --autostart`——**路径必须带引号**。
- **开发态一律拒绝**：`is_supported()` 要求 `sys.platform == "win32"` 且 `getattr(sys, "frozen", False)`。开发态写进去只会让开机去执行 python。支持条件只在门面的 `_active_impl()` 里判断一次，别在别处抄第二遍。
- **状态的唯一来源是系统**（注册表里那条值）。不要再往配置里存一份 `autostart: true`：安全软件清掉条目时会出现「开关开着但系统里没有」的双份真相。开关初值一律用 `is_enabled()` 喂。
- **`is_stale()` 管失效提示**：程序目录被移动后条目仍指向旧路径，开机自启会静默失败；设置页据此提示"关闭再开启"。
- **失败必须回滚界面**：`enable()` / `disable()` 失败抛 `SelfStartupError`，入口弹窗说明后**无论成败都用系统真值重新初始化开关**（`apply_autostart`），绝不让开关停在没生效的位置。
- 分层：设置页只发 `autostart_changed(bool)` 信号，写系统由入口做。页面里 `setValue()` 初始化期间由 `_loading` 挡住，否则"用系统真值初始化开关"本身会被当成用户操作再写一遍系统。
- **`--autostart` 是静默启动的唯一判据**：入口判断 `self_startup.AUTOSTART_FLAG in sys.argv`，命中就不 `window.show()`。这个常量同时是写进注册表那条命令的一部分，别在两处各写一遍字符串。
- **托盘是静默模式下的唯一操作面**：`NotificationService` 提供双击唤出窗口（`show_requested`）和托盘菜单「打开控制台 / 退出」（`quit_requested`）。少了它们，开机自启后用户只能去任务管理器结束进程。托盘菜单必须用属性存引用——`setContextMenu` 只挂指针，不做父子关系。

## PyInstaller 打包注意点

- 用 `class-pet.spec`（onedir + `console=False`），**不要改成 onefile**：onefile 每次启动都要解包到临时目录，桌面常驻程序启动会明显变慢。产物 `dist/class-pet/`，约 130 MB。
- **重新打包前必须关掉正在运行的 exe**：进程占用 `class-pet.exe` 与 `_internal\PySide6\plugins\*.dll`，PyInstaller 清理 `dist` 时会报 `WinError 32` / `WinError 5`。同样地，**任何以 mmap 打开该 exe 的诊断代码（如 `pefile.PE(...)`）也会锁住文件**，用完必须 `pe.close()`——实测踩过，进程列表里查不到任何 `class-pet.exe` 却删不掉。
- `qfluentwidgets` 与 `qframelesswindow` **不含任何外部数据文件**（样式内联在 Python 里），所以 `datas` 只需要图标一项；不要照搬网上"collect-data qfluentwidgets"的写法。
- spec 顶部的 `from PyInstaller.building.api import COLLECT, EXE, PYZ` / `from PyInstaller.building.build_main import Analysis` **不能删**。这四个名字本来是 PyInstaller 在执行 spec 时注入的全局变量（`build_main.py` 的 `spec_namespace` + `exec(code, spec_namespace)`），不写就会让静态检查器报 `F821 Undefined name 'Analysis'`（编辑器里表现为 `"Analysis" is not defined`）。显式 import 拿到的是同一批对象，PyInstaller 执行时会用同样的值覆盖一次，无副作用。也**不要**指望 `uv run python class-pet.spec` 能跑——正确入口只有 `uv run pyinstaller --noconfirm class-pet.spec`。
- 资源路径必须走 `resource_path("icons", "class-pet.ico")` 这种形式：它统一定位到 `<仓库根>/res/`（开发时）或 `sys._MEIPASS/res/`（打包后）。不要拼 `__file__` 相对路径，那种写法打包后必失效。
- **单实例锁名随 `sys.argv[0]` 变**（实测）：开发版是 `%TEMP%\C-Users-…-class-pet-run_classpet-class-pet.lock`，打包版是 `%TEMP%\C-Users-…-class-pet-dist-class-pet-class-pet-class-pet.lock`，两者互不影响——所以开发版和打包版可以同时运行，这是符合预期的。改入口脚本名会顺带改掉开发版的锁名。
- 图标：`res/icons/class-pet.ico` 同时用于 exe（spec 的 `icon=`）与运行时窗口图标（`app.setWindowIcon`）；它还必须进 `datas`，否则打包后 `resource_path()` 取不到。源图 `res/icons/class-pet.png` 只用于生成 ico，不打进包里。
- 打包产物 `dist/`、中间目录 `build/` 已在 `.gitignore`，不要提交。

## 验证 GUI 改动

改动界面后必须真实跑一次，不能只靠静态检查：

1. `uv run run_classpet.py` 能启动且不抛异常。
2. 无头式确认：用 `QTimer.singleShot` 挂到 `QApplication.exec` 上自动退出，再对目标控件调用 `widget.grab().save(...)`，读取该 PNG 确认渲染结果。
   - 注意：Windows 上 `screen.grabWindow(0)` 截全屏**抓不到被遮挡的窗口**，请改抓控件自身。
3. 验证打包后的 exe：`sys.frozen` 分支、图标、单实例都要在**真实 exe** 上再验一遍（开发版跑通不代表打包版跑通）。抓窗口用 Win32 `PrintWindow`：
   - `win32gui` 里**没有** `PrintWindow`，得走 ctypes：`ctypes.windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 2)`（flag `2` = `PW_RENDERFULLCONTENT`，可抓被遮挡的窗口）。
   - `GCLP_HICON` 常量在 `win32con` 里**不存在**，用字面量 `-14`。
   - 模拟"双击启动"（无控制台句柄）用 `os.startfile(exe_path)`，而不是 `subprocess.Popen`——后者会把当前进程的管道句柄继承下去，测不出真实场景。
   - **"只在打包态生效"的分支（如 `sys.frozen` 门禁）可以在探针里进程内伪造** `sys.frozen = True` 再 `runpy.run_path(入口)`，这样在开发机上就能验完整链路（例：「设置页开关 → 信号 → 入口 → 注册表」实测就是这么验的）。
   - **要真实点击 exe 界面时，先 `SetForegroundWindow` 并确认 `GetForegroundWindow()` 就是它，否则直接跳过点击**。窗口没置前就点屏幕，会点到用户自己的窗口上。
   - 会改动用户系统的验证（注册表、自启动条目）**必须自带备份与还原**，收尾要打印现场确认干净。
4. **探针脚本写进系统临时目录，不要放仓库里。** 原因：`[tool.basedpyright] include = ["**/*.py"]` 会把仓库里的临时 .py 一并分析，而这类探针必然产生误报——`QApplication.exec = patched_exec` 会被判 `reportAttributeAccessIssue`（存根里 `exec` 是 `() -> int`，补丁函数多带一个 `self`），`win.settings_page` / `win.dashboard` 这类自定义属性同样被判 `reportAttributeAccessIssue`（`topLevelWidgets()` 的静态类型只是 `QWidget`），`job.next_run_time` 还会判 `reportOptionalMemberAccess`。放临时目录可同时绕开 basedpyright 的 include、ruff 与 `uv run basedpyright` 的门禁。
   - 用法：探针里先 `sys.path.insert(0, r"<项目绝对路径>")`，再 `runpy.run_path(r"<项目绝对路径>\run_classpet.py", run_name="__main__")`。两处都不能省——`runpy.run_path` **不会**把脚本目录加进 `sys.path`，而入口要 `import classpet`；`resource_path()` 按包自身位置解析 `res/`，与 cwd 无关。
5. 验证脚本用完即删，不要留在仓库里。
