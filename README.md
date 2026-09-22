# 课小宠 ClassPet

**课小宠 ClassPet** 是一款专为教师打造的桌面助手，常驻在 Windows 与 macOS 桌面角落，以一只可爱的宠物化身陪伴老师度过每一天的教学时光。

它把**课表、调课、上课通知**这些高频琐事收进一个轻巧的桌面应用里：课表一目了然，调课一键记录、自动检测冲突，课前宠物会准时跳出来提醒“老师，下节课要开始啦”。不用再翻手机、查表格、记备忘录，所有教学安排都在桌面触手可及的地方。

课小宠，让老师少操一份心，多留一份从容。

## 环境

- Python 3.12（由 uv 管理的 `.venv`）
- PySide6 6.11.2
- qfluentwidgets 1.11.3（UI 库，PyPI 包名 `pyside6-fluent-widgets`）
- pynput 1.8.2（全局输入监听）
- tendo 0.3.0（单实例）
- apscheduler 3.11.3（定时任务，随附 tzdata、tzlocal）
- ruff 0.16.8（开发依赖，见 `[dependency-groups] dev`）
- pyinstaller 6.22.3、pillow 12.3.0（开发依赖，用于打包与生成图标）
- basedpyright 1.40.1（开发依赖，类型检查）
- 依赖声明见 `pyproject.toml`，锁定见 `uv.lock`

系统 PATH 上没有 `python`，请统一通过 `uv` 执行。

## 安装与运行

```bash
uv sync                 # 创建 .venv 并安装依赖
uv run run_classpet.py  # 启动应用
uv run pytest           # 集成测试（含"关窗后进程仍常驻"的进程级断言）
uv run ruff check .     # 静态检查
uv run basedpyright     # 类型检查
```

重复启动会被拒绝：第二个实例提示「课小宠已在运行」后以退出码 1 结束，不会开出第二个窗口。提示方式随环境而定——开发运行时写 stderr，打包后弹对话框。

**关闭窗口不等于退出程序**：`X` 只是把窗口收起来，进程继续驻留托盘（托盘图标仍在）；想再打开就双击托盘图标，或用托盘菜单「打开控制台 / 设置」。真正结束进程只有托盘菜单的「退出」一条路——所以别指望关窗能关掉它。

## 打包

```bash
uv run pyinstaller --noconfirm class-pet.spec
```

产物是 onedir 形式的 `dist/class-pet/`（约 130 MB）：`class-pet.exe` 加一个 `_internal/` 依赖目录，分发时整个 `class-pet` 目录一起拷走即可。**重新打包前必须先关闭正在运行的 exe**，否则文件被占用会失败。

图标由 `res/icons/class-pet.png`（1254×1254 源图）生成 `res/icons/class-pet.ico`（16/24/32/48/64/128/256 七种尺寸），生成命令：

```bash
uv run python -c "from PIL import Image; Image.open('res/icons/class-pet.png').save('res/icons/class-pet.ico', format='ICO', sizes=[(s,s) for s in (16,24,32,48,64,128,256)])"
```

## 开机自启动

设置页里有「开机自启动」开关。它**只在打包后的程序里可用**——开发态开关会被置灰并说明原因（开发态跑的是 `python`，写进系统没有意义）。

开启后会在 `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` 写一条：

```
"C:\...\class-pet.exe" --autostart
```

- 登录 Windows 后在托盘**静默启动，两个窗口都不显示**；双击托盘图标、或用托盘菜单「打开控制台 / 设置」唤出对应窗口。
- 关闭开关即删除该条目；重复开启等于覆盖，不会产生多条。
- 程序被移动后条目会指向旧路径，设置页会提示「登记的启动路径与当前程序不一致」，关闭再开启即可修正。
- 只写 `HKCU`，不需要管理员权限，卸载时删掉这一个值即可。
- macOS 尚未实现。

## 项目结构

```
class-pet/
├── run_classpet.py     # 入口：创建对象、连接跨模块信号、启动事件循环
├── classpet/           # 应用包
│   ├── __init__.py           # APP_NAME + 包内分层说明
│   ├── input_monitor.py      # 全局输入监听（worker）
│   ├── scheduler_worker.py   # 定时任务（worker）
│   ├── notification.py       # 托盘图标、系统通知、托盘菜单
│   ├── utils.py              # 通用工具（resource_path）
│   ├── base_window.py        # 窗口基类 AppWindow（从托盘唤出）
│   ├── self_startup/         # 开机自启动（目前只有 Windows 实现）
│   │   ├── __init__.py       # 门面：is_supported / is_enabled / enable / disable
│   │   └── win32.py          # HKCU Run 键实现
│   ├── dashboard/            # 控制台窗口
│   │   ├── window.py         # DashboardWindow
│   │   └── status_page.py    # 状态页（输入活动 + 空闲时长）
│   └── settings/             # 设置窗口
│       ├── window.py         # SettingsWindow
│       └── general_page.py   # 通用页（开机自启动开关）
├── res/                # 运行时资源
│   └── icons/
│       ├── class-pet.png     # 图标源图
│       └── class-pet.ico     # 程序与窗口图标
├── docs/
│   ├── hkcu.md         # HKCU（注册表）与开机自启的关系
│   ├── qt.md           # Qt / qfluentwidgets / 窗口与托盘的机制与实测
│   ├── workers.md      # pynput / apscheduler / tendo 的线程与单实例机制
│   └── toolchain.md    # 打包、静态检查、测试与验证手法
├── tests/              # pytest-qt 集成测试
│   ├── conftest.py     # 夹具：按入口的方式搭对象，不跑 main()
│   ├── win32util.py    # 进程级测试用的 Win32 窗口探针
│   └── test_*.py       # 窗口行为、托盘信号、状态页、自启动门禁、进程级契约
├── class-pet.spec      # PyInstaller 打包配置
├── pyproject.toml      # 项目元数据与依赖
├── uv.lock
├── AGENTS.md           # 面向编码 agent 的约定
├── README.md
└── .gitignore
```

## 当前状态

上方项目简介描述的是产品的目标形态。仓库目前的代码按职责分层放在 `classpet/` 包里（`input_monitor.py` 与 `scheduler_worker.py` 两个 worker、`notification.py` 托盘与通知、`self_startup/` 开机自启动、`dashboard/` 与 `settings/` 两个窗口、`utils.py` 工具），入口 `run_classpet.py` 只做编排：两个 `FluentWindow`（控制台 / 设置），`pynput` 全局输入监听（只统计事件次数与最后活动时间，不记录按键内容），`tendo` 保证同一份代码同时只跑一个实例，**关窗只隐藏窗口、进程常驻托盘**（退出走托盘菜单），定时任务由 `apscheduler` 承担（现有一个每分钟弹一次系统提醒的测试任务），开机自启动写 `HKCU` 的 Run 键（仅打包态可用），`class-pet.spec` 可打出带图标的 Windows 可执行程序，`tests/` 里有 27 项 pytest-qt 集成测试（含"点 X 之后进程仍常驻托盘"的进程级断言）；课表、调课、通知等业务功能均未实现。
