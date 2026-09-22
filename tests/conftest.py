"""pytest 夹具。

按入口 `run_classpet.py` 的方式把对象搭出来，但不跑 `main()`——那样会拉起真事件循环、
抢 `tendo` 单实例锁，测试就不好收敛了。窗口交给 `qtbot.addWidget` 收尾，worker 自己启停。
"""

import pytest

from classpet.dashboard.window import DashboardWindow
from classpet.input_monitor import InputMonitor
from classpet.notification import NotificationService
from classpet.settings.window import SettingsWindow


@pytest.fixture
def dashboard(qtbot):
    window = DashboardWindow()
    qtbot.addWidget(window)
    return window


@pytest.fixture
def settings_window(qtbot):
    window = SettingsWindow()
    qtbot.addWidget(window)
    return window


@pytest.fixture
def notification():
    service = NotificationService()
    yield service
    service.tray.hide()  # 托盘图标常驻，不摘掉会跨测试残留


@pytest.fixture
def monitor():
    worker = InputMonitor()
    worker.start()  # 装全局钩子
    yield worker
    worker.stop()  # 必须摘掉，否则跨测试互相干扰
