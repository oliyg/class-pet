# 打包、静态检查与验证技巧

本页是 `AGENTS.md` 里打包与验证规则的**依据**，含踩过的坑与实测输出。

## PyInstaller

- 用 `class-pet.spec`（onedir + `console=False`），产物 `dist/class-pet/` 约 130 MB。**不要改成 onefile**：onefile 每次启动都要解包到临时目录，桌面常驻程序启动会明显变慢。
- **重新打包前必须关掉正在运行的 exe**：它占用 `class-pet.exe` 与 `_internal\PySide6\plugins\*.dll`，PyInstaller 清理 `dist` 时会报 `WinError 32` / `WinError 5`。同样地，**任何以 mmap 打开该 exe 的诊断代码（如 `pefile.PE(...)`）也会锁住文件**，用完必须 `pe.close()`——实测踩过：进程列表里查不到任何 `class-pet.exe` 却删不掉。
- `qfluentwidgets` 与 `qframelesswindow` **不含任何外部数据文件**（样式内联在 Python 里），所以 `datas` 只需要图标一项；不要照搬网上 "collect-data qfluentwidgets" 的写法。
- spec 顶部的 `from PyInstaller.building.api import COLLECT, EXE, PYZ` / `from PyInstaller.building.build_main import Analysis` **不能删**。这四个名字本来是 PyInstaller 执行 spec 时注入的全局变量（`build_main.py` 的 `spec_namespace` + `exec(code, spec_namespace)`），不写就会让静态检查报 `F821 Undefined name 'Analysis'`（编辑器里表现为 `"Analysis" is not defined`）。显式 import 拿到的是同一批对象，PyInstaller 执行时会用同样的值覆盖一次，无副作用。也**不要**指望 `uv run python class-pet.spec` 能跑——正确入口只有 `uv run pyinstaller --noconfirm class-pet.spec`。
- 资源路径必须走 `resource_path("icons", "class-pet.ico")`：它统一定位到 `<仓库根>/res/`（开发时）或 `sys._MEIPASS/res/`（打包后）。不要拼 `__file__` 相对路径，那种写法打包后必失效。
- **单实例锁名随 `sys.argv[0]` 变**（实测）：开发版 `%TEMP%\C-Users-…-run_classpet-class-pet.lock`、打包版 `%TEMP%\C-Users-…-dist-class-pet-class-pet-class-pet.lock`，两者互不影响——开发版和打包版可以同时运行，这是符合预期的。改入口脚本名会顺带改掉开发版的锁名。
- 图标：`res/icons/class-pet.ico` 同时用于 exe（spec 的 `icon=`）与运行时窗口图标（`app.setWindowIcon`）；它还必须进 `datas`，否则打包后 `resource_path()` 取不到。源图 `res/icons/class-pet.png` 只用于生成 ico，不打进包里。
- 打包产物 `dist/`、中间目录 `build/` 已在 `.gitignore`，不要提交。

## basedpyright

- **严格度定在 `standard`，不是它的默认档 `recommended`。** 实测同一份代码：`recommended` = `0 error / 68 warning`，`standard` = `0 / 0`。68 条里 44 条是 `Unknown` 家族连锁，根因是 **qfluentwidgets 与 pynput 都没有类型信息**（无 `py.typed`、无 `.pyi`；PySide6 有 60 个 `.pyi`、tendo 有 `py.typed`），另有 10 条 `reportUnusedParameter`（pynput 回调参数）、8 条 `reportUnannotatedClassAttribute`、4 条 `reportUnusedCallResult`、1 条 `reportUnusedVariable`。改成 `recommended` 只会得到一墙黄色波浪线，不会挡住真问题。
- 想收紧的**正确顺序**：先给 `classpet/` 里的代码补类型注解 → 再升档。届时注意：那个承重的 `instance` 会以 `reportUnusedVariable` 出现，而 **basedpyright 不认 `# noqa: F841`**，要用 `# pyright: ignore[reportUnusedVariable]`——ruff 与 basedpyright 是两套抑制语法，别只加一边。
- `include` / `exclude` **一旦写了就是替换，不是追加**：`include` 覆盖 pyright 默认的根目录扫描（所以 `**/*.py` 与 `class-pet.spec` 必须显式列出），`exclude` 覆盖默认的 `node_modules` / `__pycache__` / 点开头目录（所以要把这三项连同 `build`、`dist` 一起列全）。
- **`class-pet.spec` 在 include 里，这是故意的**：靠 `reportUndefinedVariable` 拦住"删掉 spec 顶部 import"这类改动。实测删掉那两行 → `rc=1` + 4 条 `reportUndefinedVariable`（`Analysis` / `PYZ` / `EXE` / `COLLECT`）；补回 → `rc=0`。
- 编辑器里看到的诊断来自 Zed 自带的那份同版本 basedpyright（`%LOCALAPPDATA%\Zed\languages\basedpyright`）；项目这份由 `uv.lock` 固定，供 CI 与命令行使用。只想卡错误时用 `uv run basedpyright --level error`。

## 测试

`uv run pytest`（配置在 `pyproject.toml` 的 `[tool.pytest.ini_options]`，`qt_api = "pyside6"`）。用 pytest-qt 而不是自己驱动事件循环：`qtbot` 提供 `waitSignal` / `waitUntil` / `assertNotEmitted`，等待由信号或超时界定，不需要打 `QApplication.exec` 的补丁、也不需要 sleep 固定时长——之前那套"补丁 exec + `QTimer` 链"的探针写法既啰嗦又会引入奇怪的行为差异，已经被它取代。

夹具在 `tests/conftest.py`：按入口的方式搭对象（`DashboardWindow` / `SettingsWindow` / `NotificationService` / `InputMonitor`），但不跑 `main()`——跑 `main()` 会抢 `tendo` 单实例锁、拉起真事件循环，测试就不好收敛。窗口交给 `qtbot.addWidget` 收尾，worker 自己 `start()` / `stop()`。

两类测试：

- **组件级**：窗口收起与唤出、托盘三个信号、状态页刷新、自启动门禁、调度器状态机与"到点只发信号"。用真实控件与真实信号，断言用户能看到的结果。
- **进程级**（`tests/test_process_lifecycle.py`）：起**真实进程**（入口脚本 / 打包 exe），用 `tests/win32util.py` 的 ctypes 探针从外部断言"点 X 之后窗口仍在但不可见、进程仍活着"。组件测试只能证明窗口对象没被销毁；"进程是否常驻"必须从外部看。exe 项在没打包时自动 skip。
  - 这类测试会**先在桌面上找有没有已在运行的课小宠**，有就 skip：否则断言会打在别人（旧实例）身上——这个坑踩过一次（当时"打包版关窗后进程没了"是假警报，关掉的是旧实例的窗口）。

## 验证技巧（一次性探针）

- **打包版验行为前先确认没有旧实例在跑**：打包版遇到已有实例会弹 `QMessageBox` 并阻塞，此时桌面上的 `课小宠` 窗口属于**旧进程**，验证会打在旧构建上（踩过：关掉的是旧实例的窗口，却以为在测新构建）。先 `Get-CimInstance Win32_Process -Filter "Name='class-pet.exe'"` 清干净；要彻底隔离就把 `dist/class-pet/` 整个拷到别处再启动——锁名随路径变，天然不与任何现存实例冲突。
- 抓窗口截图用 Win32 `PrintWindow`：`win32gui` 里**没有** `PrintWindow`，得走 ctypes `ctypes.windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 2)`（flag `2` = `PW_RENDERFULLCONTENT`，可抓被遮挡的窗口）。`GCLP_HICON` 常量在 `win32con` 里**不存在**，用字面量 `-14`。
- 模拟"双击启动"（无控制台句柄）用 `os.startfile(exe_path)`，而不是 `subprocess.Popen`——后者会把当前进程的管道句柄继承下去，测不出真实场景。
- **"只在打包态生效"的分支（如 `sys.frozen` 门禁）可以在探针里进程内伪造** `sys.frozen = True` 再 `runpy.run_path(入口)`，这样在开发机上就能验完整链路（「设置页开关 → 信号 → 入口 → 注册表」实测就是这么验的）。
- **要真实点击 exe 界面时，先 `SetForegroundWindow` 并确认 `GetForegroundWindow()` 就是它**，否则直接跳过点击。窗口没置前就点屏幕，会点到用户自己的窗口上。
- 会改动用户系统的验证（注册表、自启动条目）**必须自带备份与还原**，收尾要打印现场确认干净。
- **探针脚本写进系统临时目录，不要放仓库里**：`[tool.basedpyright] include = ["**/*.py"]` 会把仓库里的临时 .py 一并分析，而这类探针必然产生误报——`QApplication.exec = patched_exec` 会被判 `reportAttributeAccessIssue`（存根里 `exec` 是 `() -> int`，补丁函数多带一个 `self`），`win.status` / `win.general` 这类自定义属性同样被判（`topLevelWidgets()` 的静态类型只是 `QWidget`），`job.next_run_time` 还会判 `reportOptionalMemberAccess`。
  - 用法：探针里先 `sys.path.insert(0, r"<项目绝对路径>")`，再 `runpy.run_path(r"<项目绝对路径>\run_classpet.py", run_name="__main__")`。两处都不能省——`runpy.run_path` **不会**把脚本目录加进 `sys.path`，而入口要 `import classpet`；`resource_path()` 按包自身位置解析 `res/`，与 cwd 无关。
