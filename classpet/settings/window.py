"""设置窗口。"""

from PySide6.QtCore import Signal
from qfluentwidgets import FluentIcon

from classpet import APP_NAME
from classpet.base_window import AppWindow
from classpet.settings.general_page import GeneralPage


class SettingsWindow(AppWindow):
    """设置窗口。

    页面只发信号；窗口把它的信号原样转发出去（`autostart_changed`），这样入口面对的是
    窗口这个门面，不必知道窗口里有哪些页面、页面内部又是什么控件。
    """

    autostart_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} · 设置")
        self.resize(640, 420)  # 初始窗口尺寸

        self.general = GeneralPage(self)
        self.addSubInterface(self.general, FluentIcon.SETTING, "通用")  # 注册进导航栏
        self.general.autostart_changed.connect(self.autostart_changed)  # 信号转发

    def setup_autostart(self, *, enabled: bool, supported: bool, stale: bool = False) -> None:
        """把系统里的自启动真值交给通用设置页。"""
        self.general.setup_autostart(enabled=enabled, supported=supported, stale=stale)
