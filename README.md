# 课小宠 ClassPet

**课小宠 ClassPet** 是一款专为教师打造的桌面助手，常驻在 Windows 与 macOS 桌面角落，以一只可爱的宠物化身陪伴老师度过每一天的教学时光。

它把**课表、调课、上课通知**这些高频琐事收进一个轻巧的桌面应用里：课表一目了然，调课一键记录、自动检测冲突，课前宠物会准时跳出来提醒“老师，下节课要开始啦”。不用再翻手机、查表格、记备忘录，所有教学安排都在桌面触手可及的地方。

课小宠，让老师少操一份心，多留一份从容。

## 环境

- Python 3.12（由 uv 管理的 `.venv`）
- PySide6 6.11.2
- qfluentwidgets 1.11.3（UI 库，PyPI 包名 `pyside6-fluent-widgets`）
- pynput 1.8.2（全局输入监听）
- 依赖声明见 `pyproject.toml`，锁定见 `uv.lock`

系统 PATH 上没有 `python`，请统一通过 `uv` 执行。

## 安装与运行

```bash
uv sync        # 创建 .venv 并安装依赖
uv run main.py # 启动应用
```

## 项目结构

```
class-pet/
├── main.py         # 唯一源文件，应用入口
├── pyproject.toml  # 项目元数据与依赖
├── uv.lock
├── AGENTS.md       # 面向编码 agent 的约定
├── README.md
└── .gitignore
```

## 当前状态

上方项目简介描述的是产品的目标形态。仓库目前只有 UI 骨架与输入的「活动监听」：`FluentWindow` + 左侧导航 + 首页，另加 `pynput` 全局输入监听（只统计事件次数与最后活动时间，不记录按键内容）；课表、调课、通知等业务功能均未实现。
