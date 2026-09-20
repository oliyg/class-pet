"""主窗口：左侧导航栏 + 右侧内容区。"""

from __future__ import annotations  # 注解不求值，类型引用可以只存在于 TYPE_CHECKING 里

from typing import TYPE_CHECKING

from qfluentwidgets import FluentIcon, FluentWindow

from classpet import APP_NAME
from classpet.dashboard.dashboard import DashboardPage
from classpet.dashboard.settings import SettingsPage

if TYPE_CHECKING:  # 只为类型标注；运行时不 import worker 模块
    from classpet.modules import InputMonitor


class MainWindow(FluentWindow):
    """主窗口。

    只负责界面装配；后台模块由入口创建后经 `setup_*` 挂进来，
    这样界面层不必知道 worker 从哪来，模块之间也不互相 import。
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(640, 420)  # 初始窗口尺寸

        self.dashboard = DashboardPage(self)
        self.addSubInterface(self.dashboard, FluentIcon.HOME, "控制台")  # 注册进导航栏

        self.settings_page = SettingsPage(self)
        self.addSubInterface(self.settings_page, FluentIcon.SETTING, "设置")

    def setup_activity(self, monitor: InputMonitor) -> None:
        """把全局输入监听接到控制台：事件计数走信号，空闲时长走取数函数。"""
        monitor.activity.connect(self.dashboard.show_activity)
        self.dashboard.setup_idle_source(monitor.idle_seconds)

    def setup_autostart(self, *, enabled: bool, supported: bool, stale: bool = False) -> None:
        """把系统里的自启动真值交给设置页。"""
        self.settings_page.setup_autostart(enabled=enabled, supported=supported, stale=stale)

    def show_and_raise(self) -> None:
        """从托盘唤出主窗口。开机自启时窗口默认不显示，这是唯一的入口。"""
        self.show()
        self.raise_()
        self.activateWindow()
