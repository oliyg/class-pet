# AGENTS.md

## 项目概览

`class-pet`（课小宠 ClassPet）：面向教师的桌面助手，目标形态是课表 / 调课 / 上课通知。PySide6 桌面端应用，**单体单文件**结构。入口为 `main.py`，当前只有一个 `QLabel` 示例窗口，业务功能尚未实现。

## 环境与命令

系统 PATH 上**没有 `python`**，`python` / `python3` 均指向 Microsoft Store 别名并报错。所有命令必须走 `uv`：

```bash
uv sync              # 同步依赖
uv run main.py       # 运行应用
uv run python -c ... # 执行临时脚本
```

- 已安装：PySide6 6.11.2（`pyside6` + `pyside6-essentials` + `pyside6-addons` + `shiboken6`）
- `pyproject.toml` 中 `package = false`：本项目是可执行的脚本目录，不是可安装包，新增模块时无需构建后端。

## 结构约束

- 保持单文件单体：除非有明确理由，新功能写进 `main.py`，不要预建 `src/`、包目录或抽象层。
- 入口保持 `main() -> int` + `if __name__ == "__main__": sys.exit(main())` 的形式。
- 不要引入未被要求的依赖、配置、脚手架或占位文件。

## 代码约定

- 缩进 4 空格，双引号，`snake_case` 命名。
- Qt 导入一律用 `PySide6.*`，不要用 `PyQt*` 或 `PySide2`。
- 未配置测试框架、linter、formatter（无 pytest / ruff / black 配置）。不要擅自引入，需要时先确认。

## 验证 GUI 改动

改动界面后必须真实跑一次，不能只靠静态检查：

1. `uv run main.py` 能启动且不抛异常。
2. 无头式确认：用 `QTimer.singleShot` 挂到 `QApplication.exec` 上自动退出，再对目标控件调用 `widget.grab().save(...)`，读取该 PNG 确认渲染结果。
   - 注意：Windows 上 `screen.grabWindow(0)` 截全屏**抓不到被遮挡的窗口**，请改抓控件自身。
3. 验证脚本用完即删，不要留在仓库里。
