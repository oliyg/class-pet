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
uv run ruff check .     # 静态检查
uv run basedpyright     # 类型检查
```

重复启动会被拒绝：第二个实例提示「课小宠已在运行」后以退出码 1 结束，不会开出第二个窗口。提示方式随环境而定——开发运行时写 stderr，打包后弹对话框。

## 打包

```bash
uv run pyinstaller --noconfirm class-pet.spec
```

产物是 onedir 形式的 `dist/class-pet/`（约 130 MB）：`class-pet.exe` 加一个 `_internal/` 依赖目录，分发时整个 `class-pet` 目录一起拷走即可。**重新打包前必须先关闭正在运行的 exe**，否则文件被占用会失败。

图标由 `res/icons/class-pet.png`（1254×1254 源图）生成 `res/icons/class-pet.ico`（16/24/32/48/64/128/256 七种尺寸），生成命令：

```bash
uv run python -c "from PIL import Image; Image.open('res/icons/class-pet.png').save('res/icons/class-pet.ico', format='ICO', sizes=[(s,s) for s in (16,24,32,48,64,128,256)])"
```

## 项目结构

```
class-pet/
├── run_classpet.py     # 入口：创建对象、连接跨模块信号、启动事件循环
├── classpet/           # 应用包
│   ├── __init__.py     # APP_NAME 等包级常量
│   ├── modules.py      # 后台 worker：InputMonitor、SchedulerWorker
│   ├── notification.py # 通知系统：常驻托盘图标 + 系统通知
│   ├── utils.py        # 通用工具（resource_path）
│   └── dashboard/      # 界面集合
│       ├── main_window.py # 主窗口：导航栏 + 页面装配
│       └── home.py        # 首页
├── res/
│   └── icons/
│       ├── class-pet.png # 图标源图
│       └── class-pet.ico # 程序与窗口图标
├── class-pet.spec      # PyInstaller 打包配置
├── pyproject.toml      # 项目元数据与依赖
├── uv.lock
├── AGENTS.md           # 面向编码 agent 的约定
├── README.md
└── .gitignore
```

## 当前状态

上方项目简介描述的是产品的目标形态。仓库目前的代码按职责分层放在 `classpet/` 包里（`modules.py` 后台 worker、`notification.py` 通知、`dashboard/` 界面、`utils.py` 工具），入口 `run_classpet.py` 只做编排：`FluentWindow` + 左侧导航 + 首页，`pynput` 全局输入监听（只统计事件次数与最后活动时间，不记录按键内容），`tendo` 保证同一份代码同时只跑一个实例，定时任务由 `apscheduler` 承担（现有一个每分钟弹一次系统提醒的测试任务），`class-pet.spec` 可打出带图标的 Windows 可执行程序；课表、调课、通知等业务功能均未实现。
