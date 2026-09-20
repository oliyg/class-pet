"""定时任务（worker）。

唤醒走 Qt 事件循环（QtScheduler 内部用 QTimer），不额外起调度线程；
但任务体跑在默认的 ThreadPoolExecutor 线程池里，所以任务里不能碰控件。
"""

from apscheduler.schedulers.qt import QtScheduler
from PySide6.QtCore import QObject, Signal, Slot

from classpet import APP_NAME


class SchedulerWorker(QObject):
    """定时任务：注册任务、启停调度器，到点只发信号。"""

    reminder_due = Signal(str, str)  # (标题, 正文)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scheduler = QtScheduler()

    def start(self) -> None:
        self.scheduler.start()
        # 测试任务：每分钟弹一次系统提醒，用来验证「调度器 → 信号 → 系统通知」整条链路。
        # 课表/提醒规则定下来后替换掉它。
        self.scheduler.add_job(self._test_reminder, "interval", minutes=1, id="test-reminder")

    @Slot()  # 接到 app.aboutToQuit
    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)  # 不让卡住的任务拖住进程退出

    def _test_reminder(self) -> None:
        # 任务体在 ThreadPoolExecutor 线程上，这里只发信号。
        self.reminder_due.emit(APP_NAME, "系统提醒测试：定时任务已触发")
