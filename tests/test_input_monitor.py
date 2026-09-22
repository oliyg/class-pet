"""全局输入监听：跨线程只发"有活动"的信号，不记录按键内容。"""

from pynput.keyboard import Controller, Key


def test_按键活动发信号_只有类别与次数(qtbot, monitor):
    keyboard = Controller()
    with qtbot.waitSignal(monitor.activity, timeout=3000) as blocker:
        keyboard.press(Key.shift)
        keyboard.release(Key.shift)

    kind, count = blocker.args
    assert kind == "键盘"
    assert count == 1  # 计数从 1 开始


def test_stop_之后再按键不再发信号(qtbot, monitor):
    monitor.stop()

    keyboard = Controller()
    with qtbot.assertNotEmitted(monitor.activity):
        keyboard.press(Key.shift)
        keyboard.release(Key.shift)
