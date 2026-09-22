"""控制台状态页：输入活动与空闲时长的显示。"""

from pynput.keyboard import Controller, Key


def test_初始文案(qtbot, dashboard):
    assert dashboard.status.activity_label.text() == "等待输入活动…"
    assert dashboard.status.idle_label.text() == "空闲：—"


def test_按键活动经信号显示到活动行(qtbot, dashboard, monitor):
    dashboard.setup_activity(monitor)

    keyboard = Controller()
    with qtbot.waitSignal(monitor.activity, timeout=3000):
        keyboard.press(Key.shift)
        keyboard.release(Key.shift)

    qtbot.waitUntil(
        lambda: dashboard.status.activity_label.text() == "最近事件：键盘 · 第 1 次", timeout=3000
    )


def test_空闲行按取数函数刷新(qtbot, dashboard):
    dashboard.status.setup_idle_source(lambda: 42.0)

    qtbot.waitUntil(lambda: dashboard.status.idle_label.text() == "空闲：42 秒", timeout=3000)


def test_空闲超过一分钟显示分秒(qtbot, dashboard):
    dashboard.status.setup_idle_source(lambda: 125.0)

    qtbot.waitUntil(lambda: dashboard.status.idle_label.text() == "空闲：2 分 5 秒", timeout=3000)
