"""全局输入监听（worker）。

不直接操作控件：回调跑在 pynput 的钩子线程上，一律通过 Qt Signal 交给界面侧处理。
"""

import itertools
import time

from pynput import keyboard, mouse
from PySide6.QtCore import QObject, Signal, Slot


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

    @Slot()  # 接到 app.aboutToQuit
    def stop(self) -> None:
        for listener in self._listeners:
            listener.stop()  # 摘下系统钩子，stop() 不可在钩子线程内调用
        self._listeners = []

    def idle_seconds(self) -> float:
        """距最后一次输入活动的秒数。

        可以被别的线程读：这里只是读一个 float，最坏读到上一个 tick 的值，无副作用。
        """
        return time.monotonic() - self.last_activity

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
