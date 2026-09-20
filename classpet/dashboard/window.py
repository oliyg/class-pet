"""控制台窗口。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from qfluentwidgets import FluentIcon

from classpet import APP_NAME
from classpet.base_window import AppWindow
from classpet.dashboard.status_page import StatusPage

if TYPE_CHECKING:  # 只为类型标注；运行时不 import worker 模块
    from classpet.input_monitor import InputMonitor


class DashboardWindow(AppWindow):
    """控制台窗口：宠物状态与活动概览。

    只负责界面装配；后台模块由入口创建后经 `setup_*` 挂进来，
    所以窗口不必知道 worker 从哪来，模块之间也不互相 import。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(APP_NAME)
        self.resize(640, 420)  # 初始窗口尺寸

        self.status = StatusPage(self)
        self.addSubInterface(self.status, FluentIcon.HOME, "状态")  # 注册进导航栏

    def setup_activity(self, monitor: InputMonitor) -> None:
        """把全局输入监听接到状态页：事件计数走信号，空闲时长走取数函数。"""
        monitor.activity.connect(self.status.show_activity)
        self.status.setup_idle_source(monitor.idle_seconds)
