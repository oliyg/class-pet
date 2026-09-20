"""通知系统：常驻托盘图标 + 系统通知弹窗。"""

from PySide6.QtCore import QObject, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QSystemTrayIcon

from classpet import APP_NAME
from classpet.utils import resource_path


class NotificationService(QObject):
    """系统通知。

    跨线程调用是安全的：只有槽里才碰控件，Qt 会把跨线程的信号投递排队回 GUI 线程。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # 托盘图标必须常驻显示，否则 showMessage 什么都不弹。
        self.tray = QSystemTrayIcon(QIcon(resource_path("icons", "class-pet.ico")), self)
        self.tray.setToolTip(APP_NAME)
        self.tray.show()

    @Slot(str, str)
    def show(self, title: str, message: str) -> None:
        self.tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 5000)
