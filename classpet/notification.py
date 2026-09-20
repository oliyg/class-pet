"""通知系统：常驻托盘图标 + 系统通知弹窗。"""

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from classpet import APP_NAME
from classpet.utils import resource_path


class NotificationService(QObject):
    """托盘图标与系统通知。

    跨线程调用是安全的：只有槽里才碰控件，Qt 会把跨线程的信号投递排队回 GUI 线程。
    托盘还承担"唤出窗口"和"退出"——开机自启时窗口不显示，这是用户唯一的操作入口。
    """

    show_requested = Signal()  # 托盘被双击：请求唤出主窗口
    quit_requested = Signal()  # 托盘菜单「退出」

    def __init__(self, parent=None):
        super().__init__(parent)
        # 托盘图标必须常驻显示，否则 showMessage 什么都不弹。
        self.tray = QSystemTrayIcon(QIcon(resource_path("icons", "class-pet.ico")), self)
        self.tray.setToolTip(APP_NAME)
        self.tray.activated.connect(self._on_activated)

        # 菜单要留着引用：setContextMenu 不做父子关系，只挂指针。
        self.menu = QMenu()
        self.menu.addAction("打开控制台", lambda *_: self.show_requested.emit())
        self.menu.addAction("退出", lambda *_: self.quit_requested.emit())
        self.tray.setContextMenu(self.menu)

        self.tray.show()

    @Slot(str, str)
    def show(self, title: str, message: str) -> None:
        self.tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 5000)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_requested.emit()
