"""窗口基类：各窗口共用的行为。"""

from PySide6.QtCore import Slot
from PySide6.QtGui import QCloseEvent
from qfluentwidgets import FluentWindow


class AppWindow(FluentWindow):
    """应用窗口基类。

    窗口公共行为放这里（从托盘唤出、关窗收起），别在每个窗口里各写一份。
    """

    @Slot()  # 接托盘的两个请求信号
    def show_and_raise(self) -> None:
        """显示窗口并置前。窗口被收起或被最小化时，这里是它唯一的入口。"""
        if self.isMinimized():
            self.showNormal()  # show() 不会还原最小化的窗口，实测 isMinimized 仍为 True
        else:
            self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event: QCloseEvent) -> None:
        """点 X 只收起窗口，不销毁它：进程常驻托盘，退出走托盘菜单「退出」。

        必须显式写：交给 Qt 默认路径的话，实测打包版会把窗口对象销毁掉，
        托盘再唤出就无处可唤（`show_and_raise` 会撞上已删除的 C++ 对象）。
        """
        event.ignore()  # 不接受关闭事件，widget 因此不会被销毁
        self.hide()
