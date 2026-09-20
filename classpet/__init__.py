"""课小宠 ClassPet —— 面向教师的桌面助手。

包内分层：
- input_monitor.py     全局输入监听（worker：只发信号、不碰控件）
- scheduler_worker.py  定时任务（worker：只发信号、不碰控件）
- notification.py      通知系统（托盘图标 + 系统通知）
- base_window.py       窗口基类（AppWindow）
- dashboard/           控制台窗口与它的页面
- settings/            设置窗口与它的页面
- utils.py             通用工具

每个窗口一个子包：包内 window.py 是窗口本体，*_page.py 是它装载的页面。
"""

APP_NAME = "课小宠 ClassPet"
