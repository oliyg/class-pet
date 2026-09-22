"""窗口基类的共同行为：从托盘唤出、关窗收起（不销毁）。

"关窗收起"是常驻托盘的核心契约：窗口对象若被销毁，托盘就再也唤不回来。
"""

import ctypes
import sys

import pytest

WM_CLOSE = 0x0010
win_only = pytest.mark.skipif(not sys.platform.startswith("win"), reason="WM_CLOSE 是 Windows 路径")


def test_唤出显示窗口(qtbot, dashboard):
    dashboard.hide()

    dashboard.show_and_raise()

    assert dashboard.isVisible()


def test_唤出还原最小化的窗口(qtbot, dashboard):
    dashboard.show()
    dashboard.showMinimized()
    qtbot.waitUntil(lambda: dashboard.isMinimized(), timeout=3000)

    dashboard.show_and_raise()

    assert dashboard.isVisible()
    assert not dashboard.isMinimized()


def test_qt关窗只收起_还能再唤出(qtbot, dashboard):
    dashboard.show()
    dashboard.close()

    assert not dashboard.isVisible()
    dashboard.show_and_raise()  # 对象被销毁的话这里会抛 RuntimeError
    assert dashboard.isVisible()


@win_only
def test_原生关窗也只收起_还能再唤出(qtbot, dashboard):
    dashboard.show()
    qtbot.waitUntil(lambda: dashboard.isVisible(), timeout=3000)

    ctypes.windll.user32.PostMessageW(int(dashboard.winId()), WM_CLOSE, 0, 0)
    qtbot.waitUntil(lambda: not dashboard.isVisible(), timeout=3000)

    dashboard.show_and_raise()
    assert dashboard.isVisible()


def test_设置窗口同样只收起(qtbot, settings_window):
    settings_window.show()
    settings_window.close()

    assert not settings_window.isVisible()
    settings_window.show_and_raise()
    assert settings_window.isVisible()
