# AGENTS.md

## 项目概览

`class-pet`（课小宠 ClassPet）：面向教师的桌面助手，目标形态是课表 / 调课 / 上课通知。PySide6 桌面端应用，UI 层用 **qfluentwidgets**，**单体单文件**结构。入口为 `main.py`，当前是 `FluentWindow` + 单个首页 + `pynput` 全局输入监听的骨架，业务功能尚未实现。

## 环境与命令

系统 PATH 上**没有 `python`**，`python` / `python3` 均指向 Microsoft Store 别名并报错。所有命令必须走 `uv`：

```bash
uv sync              # 同步依赖
uv run main.py       # 运行应用
uv run python -c ... # 执行临时脚本
uv run ruff check .  # 静态检查
```

- 已安装：PySide6 6.11.2（`pyside6` + `pyside6-essentials` + `pyside6-addons` + `shiboken6`）
- 已安装 UI 库：qfluentwidgets 1.11.3（PyPI 包名 `pyside6-fluent-widgets`），随之带入 `pysidesix-frameless-window`、`darkdetect`、`pywin32`。
- 已安装输入监听：pynput 1.8.2（随附 `six`）。
- 已安装单实例：tendo 0.3.0。
- `pyproject.toml` 中 `package = false`：本项目是可执行的脚本目录，不是可安装包，新增模块时无需构建后端。

## 结构约束

- 保持单文件单体：除非有明确理由，新功能写进 `main.py`，不要预建 `src/`、包目录或抽象层。
- 入口保持 `main() -> int` + `if __name__ == "__main__": sys.exit(main())` 的形式。
- 不要引入未被要求的依赖、配置、脚手架或占位文件。

## 代码约定

- 缩进 4 空格，双引号，`snake_case` 命名。
- Qt 导入一律用 `PySide6.*`，不要用 `PyQt*` 或 `PySide2`。
- UI 控件优先用 `qfluentwidgets`（`FluentWindow`、`PushButton`、`BodyLabel`、`SubtitleLabel` 等）；`PySide6.QtWidgets` 只用来搭布局与容器（`QWidget`、`QVBoxLayout`）。同一控件两套写法混用属于禁止项。
- 未配置测试框架与 formatter（无 pytest / black）。已引入 ruff 做静态检查（`uv run ruff check .`），不要换别的 linter，也不要擅自加规则。
- **禁止 `ruff check --fix --unsafe-fixes`**：其中「移除未使用的 `instance`」会静默破坏单实例（见下）。

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
- 第二个实例目前只往 stderr 写一行并返回 1，GUI 用户看不到提示。若要做"唤出已有窗口"，需要另加 IPC（`QLocalServer`/`QSharedMemory`），`tendo` 不提供。

## 验证 GUI 改动

改动界面后必须真实跑一次，不能只靠静态检查：

1. `uv run main.py` 能启动且不抛异常。
2. 无头式确认：用 `QTimer.singleShot` 挂到 `QApplication.exec` 上自动退出，再对目标控件调用 `widget.grab().save(...)`，读取该 PNG 确认渲染结果。
   - 注意：Windows 上 `screen.grabWindow(0)` 截全屏**抓不到被遮挡的窗口**，请改抓控件自身。
3. 验证脚本用完即删，不要留在仓库里。
