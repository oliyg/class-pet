"""窗口基类：各窗口共用的行为。"""

from PySide6.QtCore import Slot
from qfluentwidgets import FluentWindow


class AppWindow(FluentWindow):
    """应用窗口基类。

    目前只有"从托盘唤出"这一个共同行为。以后窗口的公共行为（例如关闭到托盘）
    也放这里，别在每个窗口里各写一份。
    """

    @Slot()  # 接托盘的两个请求信号
    def show_and_raise(self) -> None:
        """显示窗口并置前。开机自启时不显示窗口，这里是它唯一的入口。"""
        self.show()
        self.raise_()
        self.activateWindow()
