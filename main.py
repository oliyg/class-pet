# 课小宠 ClassPet —— 单体单文件应用，全部逻辑都写在本文件内。
import itertools
import os
import sys
import time

from apscheduler.schedulers.qt import QtScheduler
from pynput import keyboard, mouse
from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QMessageBox,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

# UI 控件统一取自 qfluentwidgets，PySide6.QtWidgets 只用于布局与容器。
from qfluentwidgets import (
    BodyLabel,
    FluentIcon,
    FluentWindow,
    PushButton,
    SubtitleLabel,
    Theme,
    setTheme,
)
from tendo import singleton


def resource_path(relative: str) -> str:
    """资源定位：开发时在脚本旁边，PyInstaller 打包后在 sys._MEIPASS 下。"""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


class InputMonitor(QObject):
    """全局输入监听：只统计“有活动”，不记录具体按了哪个键。"""

    # (事件类别, 该类别累计次数)。从系统钩子线程发出，Qt 会自动排队到 GUI 线程。
    activity = Signal(str, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._keyboard_count = itertools.count(1)  # next() 是原子操作，跨线程无需加锁
        self._mouse_count = itertools.count(1)
        self._listeners = []
        self.last_activity = time.monotonic()  # 时间戳，供后续做空闲判断

    def start(self) -> None:
        self._listeners = [
            keyboard.Listener(on_press=self._on_key_press),
            mouse.Listener(
                on_click=self._on_click,
                on_scroll=self._on_scroll,
                on_move=self._on_move,
            ),
        ]
        for listener in self._listeners:
            listener.start()  # 各自跑在独立的守护线程上

    def stop(self) -> None:
        for listener in self._listeners:
            listener.stop()  # 摘下系统钩子，stop() 不可在钩子线程内调用
        self._listeners = []

    def _on_key_press(self, key) -> None:
        # 故意不读 key.char：全局记录按键内容等同于键盘记录器。
        # 注意回调不能返回 False，pynput 会把它当停表信号抛 StopException。
        self._emit("键盘", self._keyboard_count)

    def _on_click(self, x, y, button, pressed) -> None:
        if pressed:  # 一次点击回调两次（按下 + 抬起），只计按下
            self._emit("鼠标点击", self._mouse_count)

    def _on_scroll(self, x, y, dx, dy) -> None:
        self._emit("鼠标滚轮", self._mouse_count)

    def _on_move(self, x, y) -> None:
        # 鼠标移动频率极高，只刷新时间戳不发信号，避免刷爆事件循环。
        self.last_activity = time.monotonic()

    def _emit(self, kind: str, counter) -> None:
        self.last_activity = time.monotonic()
        self.activity.emit(kind, next(counter))


class HomePage(QWidget):
    """首页占位页面。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        # addSubInterface 要求 objectName 非空，否则抛 ValueError。
        self.setObjectName("homePage")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)  # 内容区留白，避免控件贴边
        layout.setSpacing(12)  # 相邻控件之间的间距

        title = SubtitleLabel(self)
        title.setText("课小宠 ClassPet")
        layout.addWidget(title)

        greeting = BodyLabel(self)
        greeting.setText("Hello, qfluentwidgets!")
        layout.addWidget(greeting)

        # 1.11.3 的构造函数只收 parent，文本必须用 setText 赋值。
        button = PushButton(self)
        button.setText("确定")
        layout.addWidget(button)

        self.activity_label = BodyLabel(self)  # 由 InputMonitor 的信号驱动更新
        self.activity_label.setText("全局输入监听：未启动")
        layout.addWidget(self.activity_label)

        layout.addStretch(1)  # 吸收剩余高度，让控件从上往下排列

    def show_activity(self, kind: str, count: int) -> None:
        self.activity_label.setText(f"最近事件：{kind} · 第 {count} 次")


class ReminderService(QObject):
    """系统提醒：调度器任务只发信号，真正的通知在 GUI 线程弹出。"""

    notify = Signal(str, str)  # (标题, 正文)

    def __init__(self, parent=None):
        super().__init__(parent)
        # 托盘图标必须常驻显示，否则 showMessage 不弹任何东西。
        self.tray = QSystemTrayIcon(QIcon(resource_path("assets/class-pet.ico")), self)
        self.tray.setToolTip("课小宠 ClassPet")
        self.tray.show()
        self.notify.connect(self._show)  # 跨线程连接，Qt 自动排队回 GUI 线程

    def remind(self, title: str, message: str) -> None:
        """供调度器任务调用。任务跑在 ThreadPoolExecutor 线程上，这里只发信号、不碰控件。"""
        self.notify.emit(title, message)

    def _show(self, title: str, message: str) -> None:
        self.tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 5000)


class MainWindow(FluentWindow):
    """主窗口：左侧导航栏 + 右侧内容区。"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("课小宠 ClassPet")
        self.resize(640, 420)  # 初始窗口尺寸

        # 保留为属性，便于后续切页或访问该页面。
        self.home_page = HomePage(self)
        self.addSubInterface(self.home_page, FluentIcon.HOME, "首页")  # 注册进导航栏

        self.monitor = InputMonitor(self)  # 监听器归主窗口所有，随窗口一起销毁
        self.monitor.activity.connect(self.home_page.show_activity)

        # 定时任务调度器：唤醒走 Qt 事件循环（内部用 QTimer.singleShot），不额外起调度线程。
        # 但任务体跑在默认的 ThreadPoolExecutor 线程池里，所以任务里同样不能直接碰控件，
        # 必须经 Signal 回到 GUI 线程（与 InputMonitor 同一条规矩）。
        # 它不是 QObject、挂不了父对象，启停由 main() 显式负责。
        self.scheduler = QtScheduler()

        self.reminders = ReminderService(self)

        # 测试任务：每分钟弹一次系统提醒，用来验证「调度器 → 信号 → 系统通知」整条链路。
        # 等课表/提醒规则确定后替换掉（args 由调度器传入，不用 lambda 便于排查）。
        self.scheduler.add_job(
            self.reminders.remind,
            "interval",
            minutes=1,
            id="test-reminder",
            args=("课小宠 ClassPet", "系统提醒测试：定时任务已触发"),
        )


def report_already_running() -> None:
    """告知用户已有实例在运行。

    打包后（`sys.frozen`）进程没有控制台，往 stderr 写等于石沉大海，必须弹对话框；
    开发时保持只写 stderr，方便脚本与终端观察。
    """
    if not getattr(sys, "frozen", False):
        print("课小宠 ClassPet 已在运行，本次启动退出。", file=sys.stderr)
        return

    _app = QApplication(sys.argv)  # QMessageBox 需要先有 QApplication，引用要保留以免被回收
    QMessageBox.information(None, "课小宠 ClassPet", "课小宠已在运行，请勿重复启动。")


def main() -> int:
    # 单实例：锁文件放在系统临时目录，第二个实例会抛 SingleInstanceException。
    # 必须留住 instance 这个引用——对象一旦被回收，__del__ 会立刻删掉锁文件，单实例随即失效。
    try:
        instance = singleton.SingleInstance("class-pet")  # noqa: F841 —— 见上：这个引用不能删
    except singleton.SingleInstanceException:
        # 已有实例在运行：不用再启动 Qt 主流程，直接退出。
        report_already_running()
        return 1

    # 高 DPI 缩放策略必须在 QApplication 构造之前设置，否则不生效。
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("assets/class-pet.ico")))  # 任务栏 / Alt-Tab 图标
    setTheme(Theme.AUTO)  # 主题跟随系统明暗

    window = MainWindow()
    window.show()  # 先显示窗口，再进入事件循环
    window.monitor.start()  # 窗口就绪后再挂全局钩子
    window.scheduler.start()  # 依附 Qt 事件循环，必须在 app.exec() 之前启动
    app.aboutToQuit.connect(window.monitor.stop)  # 退出前务必摘下钩子
    # wait=False：不让卡住的任务拖住进程退出；提醒类任务被中途截断无副作用
    app.aboutToQuit.connect(lambda: window.scheduler.shutdown(wait=False))

    return app.exec()  # 阻塞至窗口关闭，返回进程退出码


if __name__ == "__main__":
    sys.exit(main())
