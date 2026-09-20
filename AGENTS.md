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
uv run pyinstaller --noconfirm class-pet.spec  # 打包（先关掉正在运行的 exe）
```

- 已安装：PySide6 6.11.2（`pyside6` + `pyside6-essentials` + `pyside6-addons` + `shiboken6`）
- 已安装 UI 库：qfluentwidgets 1.11.3（PyPI 包名 `pyside6-fluent-widgets`），随之带入 `pysidesix-frameless-window`、`darkdetect`、`pywin32`。
- 已安装输入监听：pynput 1.8.2（随附 `six`）。
- 已安装单实例：tendo 0.3.0。
- 开发依赖（`[dependency-groups] dev`）：ruff 0.16.8、pyinstaller 6.22.3、pillow 12.3.0。
- `pyproject.toml` 中 `package = false`：本项目是可执行的脚本目录，不是可安装包，新增模块时无需构建后端。

## 结构约束

- 保持单文件单体：除非有明确理由，新功能写进 `main.py`，不要预建 `src/`、包目录或抽象层。
- 现有非源码文件只有 `class-pet.spec`（打包配置）与 `assets/`（图标），不要再扩目录。`assets/` 里的路径引用一律经 `resource_path()`。
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
- 第二个实例的提示由 `report_already_running()` 按环境分流：`getattr(sys, "frozen", False)` 为真（打包后没有控制台）就弹 `QMessageBox`，否则写 stderr。若要做"唤出已有窗口"，需要另加 IPC（`QLocalServer`/`QSharedMemory`），`tendo` 不提供。

## PyInstaller 打包注意点

- 用 `class-pet.spec`（onedir + `console=False`），**不要改成 onefile**：onefile 每次启动都要解包到临时目录，桌面常驻程序启动会明显变慢。产物 `dist/class-pet/`，约 130 MB。
- **重新打包前必须关掉正在运行的 exe**：进程占用 `class-pet.exe` 与 `_internal\PySide6\plugins\*.dll`，PyInstaller 清理 `dist` 时会报 `WinError 32` / `WinError 5`。同样地，**任何以 mmap 打开该 exe 的诊断代码（如 `pefile.PE(...)`）也会锁住文件**，用完必须 `pe.close()`——实测踩过，进程列表里查不到任何 `class-pet.exe` 却删不掉。
- `qfluentwidgets` 与 `qframelesswindow` **不含任何外部数据文件**（样式内联在 Python 里），所以 `datas` 只需要图标一项；不要照搬网上"collect-data qfluentwidgets"的写法。
- spec 顶部的 `from PyInstaller.building.api import COLLECT, EXE, PYZ` / `from PyInstaller.building.build_main import Analysis` **不能删**。这四个名字本来是 PyInstaller 在执行 spec 时注入的全局变量（`build_main.py` 的 `spec_namespace` + `exec(code, spec_namespace)`），不写就会让静态检查器报 `F821 Undefined name 'Analysis'`（编辑器里表现为 `"Analysis" is not defined`）。显式 import 拿到的是同一批对象，PyInstaller 执行时会用同样的值覆盖一次，无副作用。也**不要**指望 `uv run python class-pet.spec` 能跑——正确入口只有 `uv run pyinstaller --noconfirm class-pet.spec`。
- 资源路径必须走 `resource_path()`（打包后取 `sys._MEIPASS`）。直接用 `__file__` 相对路径的开发写法在打包后会失效。
- **单实例锁名随 `sys.argv[0]` 变**：开发版锁是 `...-class-pet-main-class-pet.lock`，打包版是 `...-class-pet-dist-class-pet-class-pet-class-pet.lock`，两者互不影响——所以开发版和打包版可以同时运行，这是符合预期的。
- 图标：`assets/class-pet.ico` 同时用于 exe（spec 的 `icon=`）与运行时窗口图标（`app.setWindowIcon`）。源图 `assets/class-pet.png` 只用于生成 ico，不打进包里。
- 打包产物 `dist/`、中间目录 `build/` 已在 `.gitignore`，不要提交。

## 验证 GUI 改动

改动界面后必须真实跑一次，不能只靠静态检查：

1. `uv run main.py` 能启动且不抛异常。
2. 无头式确认：用 `QTimer.singleShot` 挂到 `QApplication.exec` 上自动退出，再对目标控件调用 `widget.grab().save(...)`，读取该 PNG 确认渲染结果。
   - 注意：Windows 上 `screen.grabWindow(0)` 截全屏**抓不到被遮挡的窗口**，请改抓控件自身。
3. 验证打包后的 exe：`sys.frozen` 分支、图标、单实例都要在**真实 exe** 上再验一遍（开发版跑通不代表打包版跑通）。抓窗口用 Win32 `PrintWindow`：
   - `win32gui` 里**没有** `PrintWindow`，得走 ctypes：`ctypes.windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 2)`（flag `2` = `PW_RENDERFULLCONTENT`，可抓被遮挡的窗口）。
   - `GCLP_HICON` 常量在 `win32con` 里**不存在**，用字面量 `-14`。
   - 模拟"双击启动"（无控制台句柄）用 `os.startfile(exe_path)`，而不是 `subprocess.Popen`——后者会把当前进程的管道句柄继承下去，测不出真实场景。
4. 验证脚本用完即删，不要留在仓库里。
