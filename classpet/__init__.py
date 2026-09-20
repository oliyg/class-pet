"""课小宠 ClassPet —— 面向教师的桌面助手。

包内分层：
- modules.py      后台 worker（输入监听、定时任务），只发信号、不碰控件
- notification.py 通知系统（托盘图标 + 系统通知）
- dashboard/      界面集合（主窗口与各功能页面）
- utils.py        通用工具
"""

APP_NAME = "课小宠 ClassPet"
