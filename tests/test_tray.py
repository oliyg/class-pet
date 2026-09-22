"""托盘：菜单项与三个"用户意图"信号。

托盘是开机自启后用户唯一的操作面，这三个信号一个都不能少、也不能接错。
"""

from PySide6.QtWidgets import QSystemTrayIcon

from classpet.notification import NotificationService


def trigger_menu(service: NotificationService, label: str) -> None:
    for action in service.menu.actions():
        if action.text() == label:
            action.trigger()
            return
    raise AssertionError(f"托盘菜单里没有「{label}」")


def test_菜单三项齐全(notification):
    assert [action.text() for action in notification.menu.actions()] == ["打开控制台", "设置", "退出"]


def test_托盘图标已显示(notification):
    # 不 show 出来，showMessage 什么都不弹。
    assert notification.tray.isVisible()


def test_双击托盘请求打开控制台(qtbot, notification):
    with qtbot.waitSignal(notification.dashboard_requested, timeout=2000):
        notification.tray.activated.emit(QSystemTrayIcon.ActivationReason.DoubleClick)


def test_单击托盘不请求打开控制台(qtbot, notification):
    with qtbot.assertNotEmitted(notification.dashboard_requested):
        notification.tray.activated.emit(QSystemTrayIcon.ActivationReason.Trigger)


def test_菜单打开控制台(qtbot, notification):
    with qtbot.waitSignal(notification.dashboard_requested, timeout=2000):
        trigger_menu(notification, "打开控制台")


def test_菜单设置(qtbot, notification):
    with qtbot.waitSignal(notification.settings_requested, timeout=2000):
        trigger_menu(notification, "设置")


def test_菜单退出(qtbot, notification):
    with qtbot.waitSignal(notification.quit_requested, timeout=2000):
        trigger_menu(notification, "退出")
