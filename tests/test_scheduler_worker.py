"""定时任务：启停状态机，以及"到点只发信号"的跨线程契约。"""

from datetime import UTC, datetime, timedelta

import pytest
from apscheduler.schedulers.base import SchedulerAlreadyRunningError

from classpet.scheduler_worker import SchedulerWorker


def test_到点通过信号通知界面(qtbot):
    """任务体跑在 ThreadPoolExecutor 线程上，只能 emit；这里验证它确实能到 GUI 线程。"""
    worker = SchedulerWorker()
    worker.start()
    try:
        with qtbot.waitSignal(worker.reminder_due, timeout=5000) as blocker:
            worker.scheduler.add_job(
                lambda: worker.reminder_due.emit("测试标题", "测试正文"),
                "date",
                run_date=datetime.now(UTC) + timedelta(milliseconds=200),
            )
        assert blocker.args == ["测试标题", "测试正文"]
    finally:
        worker.shutdown()


def test_重复启动抛错():
    worker = SchedulerWorker()
    worker.start()
    try:
        with pytest.raises(SchedulerAlreadyRunningError):
            worker.start()
    finally:
        worker.shutdown()


def test_没启动过也能安全关闭_之后还能启动(qtbot):
    """退出路径（aboutToQuit）可能没经历过启动路径，shutdown() 必须可安全重复调用。"""
    worker = SchedulerWorker()

    worker.shutdown()
    worker.start()
    try:
        assert worker.scheduler.running
    finally:
        worker.shutdown()
