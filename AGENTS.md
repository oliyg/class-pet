# AGENTS.md

## 项目概览

**class-pet（课小宠 ClassPet）**：面向教师的桌面助手，目标形态是课表 / 调课 / 上课通知。PySide6 + **qfluentwidgets**，业务在 `classpet/` 包。现为骨架：两个 `FluentWindow`（控制台 / 设置）、全局输入监听、定时提醒、开机自启动、托盘常驻；业务未实现。

## 细节索引

本文件只留**必须怎么做**；机制、证据与实测输出在 `docs/`，改相关代码前先读对应那页。新增机制类说明也写进 `docs/`，别往这里塞。

| 主题 | 文档 |
|---|---|
| Qt / qfluentwidgets / 窗口与托盘生命周期 / `@Slot` 的依据 | `docs/qt.md` |
| pynput 钩子线程、apscheduler 任务线程、tendo 单实例机制 | `docs/workers.md` |
| PyInstaller 打包、basedpyright 配置、测试与验证手法 | `docs/toolchain.md` |
| HKCU 注册表与开机自启的关系 | `docs/hkcu.md` |

## 环境与命令

PATH 上**没有 `python`**（`python` / `python3` 都是 Store 别名，报错），一律走 `uv`。

```bash
uv sync
uv run run_classpet.py                          # 运行
uv run python -c ...                            # 临时脚本
uv run ruff check .                             # 静态检查
uv run basedpyright                             # 类型检查
uv run pyinstaller --noconfirm class-pet.spec   # 打包（先关掉正在跑的 exe）
```

依赖：PySide6 6.11.2、qfluentwidgets 1.11.3（PyPI 名 `pyside6-fluent-widgets`）、pynput 1.8.2、tendo 0.3.0、apscheduler 3.11.3；dev：ruff 0.16.8、basedpyright 1.40.1、pyinstaller 6.22.3、pillow 12.3.0。`pyproject.toml` 的 `package = false`：本仓库是可执行脚本目录、不是可安装包，加模块不用配构建后端。

## 结构约束

- 按职责分层（参照 DyberPet），不要退化回单文件。`run_classpet.py` 只做编排：建对象、连跨模块信号、启停、进事件循环。
- worker 各自一个模块（`classpet/input_monitor.py`、`classpet/scheduler_worker.py`），只发信号、不碰控件；`notification.py` 通知、`utils.py` 工具、`base_window.py` 窗口公共行为。
- 界面**每个窗口一个子包**（`dashboard/`、`settings/`）：包内 `window.py` 是窗口本体、`*_page.py` 是它装载的页面。**没有 `ui/` 这一层**，窗口包直接挂在 `classpet/` 下。
- `res/` 放运行时资源、按类型分子目录；平台相关功能各自子包（`self_startup/`：门面 + `win32.py`），门面按 `sys.platform` 分发，**没实现的平台不要留空实现或占位文件**。
- **模块之间不互相 import**：worker 与界面靠 Signal 连接，连线统一写在入口；界面要用外部模块走 `setup_*` 钩子，别自己 new 后台对象。
- 入口保持 `main() -> int` + `if __name__ == "__main__": sys.exit(main())`；不引入未被要求的依赖、配置、脚手架、空目录、占位文件。
- 命名占用：`classpet/settings/` 已归"设置窗口"，将来做配置持久化用 `config.py` 之类。
- 机制类说明写 `docs/`，README 只留使用者需要的内容；新增 docs 同步补 README 目录树。
- 测试放 `tests/`：`conftest.py` 夹具 + `test_*.py`，Win32 辅助放 `tests/win32util.py`；别把测试脚本塞进 `classpet/`。

## 代码约定

- 缩进 4 空格、双引号；函数 / 变量 / 模块 `snake_case`，类 `PascalCase`，私有成员单下划线前缀。Qt 导入只用 `PySide6.*`。
- **接信号的方法一律加 `@Slot(...)`**，签名与所连信号一致；不接信号的不加（`setup_*` / `start()` 这类被直接调用的）；自由函数、lambda、信号转发连接不加。**签名写错比不写更糟**——跨线程排队投递靠它做参数转换，依据见 `docs/qt.md`。
- UI 优先 `qfluentwidgets`（`FluentWindow`、`PushButton`、`BodyLabel`…），`PySide6.QtWidgets` 只用来搭布局与容器；同一控件两套写法混用是禁止项。**有意偏离、不要扩大**：托盘只能用原生 `QSystemTrayIcon` / `QMenu`；启动早期与失败路径用原生 `QMessageBox`。
- **测试框架是 pytest + pytest-qt**（`uv run pytest`），别再引别的。GUI 测试用 `qtbot` 的 `waitSignal` / `waitUntil` / `assertNotEmitted` 等原语，**不要打 `QApplication.exec` 的补丁、不要 sleep 固定时长**（那是探针时代的写法，等待必须由信号或轮询超时来界定）；要验进程级行为（关窗常驻托盘）就起真实进程，别在进程内模拟。静态检查只认 ruff（别换 linter、别擅自加规则），**禁止 `--unsafe-fixes`**（它会移除承重的 `instance`，静默破坏单实例）。类型检查用 basedpyright，**别把它调成 `recommended`**；配置与抑制语法见 `docs/toolchain.md`。

## worker 与线程规矩

- **GUI 之外的回调 / 任务一律只 `emit` 信号，绝不碰控件**：pynput 回调在钩子线程，apscheduler 任务体在 `ThreadPoolExecutor`（`QtScheduler`（`apscheduler.schedulers.qt`）只负责"何时唤醒"，不等于任务在 GUI 线程）。
- **成对启停**：`InputMonitor.start()` ↔ `app.aboutToQuit.connect(monitor.stop)`，`SchedulerWorker.start()` ↔ `aboutToQuit.connect(scheduler.shutdown)`；`stop()` 不在钩子线程内调用。
- 各库的坑（pynput 回调参数个数自动适配、返回 `False` 会终止监听、跨线程计数用 `itertools.count()`、`monotonic()` 粒度 15.625 ms、别读 `key.char`；apscheduler 的状态机与版本、别拿它刷界面；tendo 必须持引用）见 `docs/workers.md`。

## 开机自启动注意点

- 代码在 `classpet/self_startup/`：`__init__.py` 是门面（`is_supported` / `is_enabled` / `is_stale` / `enable` / `disable` / `AUTOSTART_FLAG`），`win32.py` 用 `winreg` 读写 HKCU Run 键；macOS 未实现——要加就新建 `darwin.py` 并接进门面的平台分发。
- **只写 `HKCU`，绝不写 `HKLM`**（后者要管理员）；值名 `ClassPet`，形如 `"<exe 路径>" --autostart`，**路径必须带引号**。
- **开发态一律拒绝**：`is_supported()` 要求 `sys.platform == "win32"` 且 `getattr(sys, "frozen", False)`，判断只在门面的 `_active_impl()` 里做一次。
- **状态的唯一来源是系统**（注册表那条值）：不要再往配置里存 `autostart: true`，开关初值一律用 `is_enabled()` 喂；`is_stale()` 负责"登记路径与当前程序不一致"的提示。
- **失败必须回滚界面**：`enable()` / `disable()` 失败抛 `SelfStartupError`，入口弹窗后**无论成败都用系统真值重新初始化开关**。
- 分层：通用设置页只发 `autostart_changed(bool)`，窗口原样转发，写系统由入口做；页面里 `setValue()` 初始化期间用 `_loading` 挡住，否则会把"初始化"当成用户操作再写一遍系统。
- **`--autostart` 是静默启动的唯一判据**：命中就两个窗口都不 `show()`（只留托盘）；该常量同时是注册表命令的一部分，别两处各写一遍字符串。
- **托盘是静默模式下的唯一操作面**：双击 / 菜单开控制台（`dashboard_requested`）、菜单开设置（`settings_requested`）、退出（`quit_requested`）一个都不能少；托盘菜单必须用属性存引用。
- **关窗 ≠ 退出，而且必须显式收起**：入口 `app.setQuitOnLastWindowClosed(False)` 别改回默认值；`AppWindow.closeEvent` 的 `event.ignore()` + `hide()` 不能省（默认路径在打包版会销毁窗口对象、开发版却只是隐藏，见 `docs/qt.md`）；退出的唯一入口是托盘菜单「退出」。
- **从托盘唤出必须先还原最小化**：`AppWindow.show_and_raise()` 里的 `isMinimized()` 分支不能省。

## PyInstaller 打包注意点

- 用 `class-pet.spec`（onedir + `console=False`），**不要改 onefile**；产物 `dist/class-pet/` 约 130 MB。
- **打包前必须关掉正在跑的 exe**（占用 `class-pet.exe` 与 `_internal\PySide6\plugins\*.dll`），**也别用 mmap 打开该 exe 的诊断代码**（`pefile.PE(...)` 会锁住文件，用完必须 `close()`）。
- spec 顶部的 `from PyInstaller.building.api import COLLECT, EXE, PYZ` / `...build_main import Analysis` **不能删**；`datas` 只需要图标一项（qfluentwidgets 不含外部数据文件）；资源路径必须走 `resource_path(...)`。细节见 `docs/toolchain.md`。
- 图标 `res/icons/class-pet.ico` 同时给 exe 与运行时窗口图标，且必须进 `datas`；`dist/`、`build/` 已在 `.gitignore`。

## 验证 GUI 改动

改界面后必须真跑一次，不能只靠静态检查：

1. `uv run pytest` —— 组件级行为（窗口收起/唤出、托盘信号、状态页刷新、自启动门禁）与进程级契约（关窗后进程仍活着）都在里面，`11s` 左右跑完。
2. 打包之后**再跑一次**（`tests/test_process_lifecycle.py` 里的 exe 项会自动执行，没打包时自动跳过）：开发版跑通不代表打包版跑通，关窗收起这类行为两边就曾经不一致。
3. 一次性探针（临时查一个具体问题）写进系统临时目录、用完即删，别放进 `tests/`；命令与坑见 `docs/toolchain.md`。

用户可见的界面改动还要肉眼看一次渲染结果：`widget.grab().save(...)` 存 PNG 再读图（`screen.grabWindow(0)` 截全屏**抓不到被遮挡的窗口**）。
