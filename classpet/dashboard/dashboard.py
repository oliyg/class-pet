"""控制台：宠物状态与活动概览。"""

from collections.abc import Callable

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QVBoxLayout, QWidget
from qfluentwidgets import BodyLabel, SubtitleLabel

from classpet import APP_NAME


class DashboardPage(QWidget):
    """控制台页。

    目前展示两类真实状态：全局输入活动（由 InputMonitor 的信号驱动）与空闲时长
    （由入口注入取数函数，本页不 import worker 模块）。宠物状态等内容待有数据源再加。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # addSubInterface 要求 objectName 非空，否则抛 ValueError。
        self.setObjectName("dashboardPage")

        self._idle_source: Callable[[], float] | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)  # 内容区留白，避免控件贴边
        layout.setSpacing(12)  # 相邻控件之间的间距

        title = SubtitleLabel(self)
        title.setText("控制台")
        layout.addWidget(title)

        subtitle = BodyLabel(self)
        subtitle.setText(APP_NAME)
        layout.addWidget(subtitle)

        self.activity_label = BodyLabel(self)  # 由 InputMonitor 的信号驱动更新
        self.activity_label.setText("等待输入活动…")
        layout.addWidget(self.activity_label)

        self.idle_label = BodyLabel(self)
        self.idle_label.setText("空闲：—")
        layout.addWidget(self.idle_label)

        layout.addStretch(1)  # 吸收剩余高度，让控件从上往下排列

        # 空闲时长每秒刷新一次。用 QTimer 而不是调度器：这只是界面刷新，不是定时任务。
        self._idle_timer = QTimer(self)
        self._idle_timer.setInterval(1000)
        self._idle_timer.timeout.connect(self._refresh_idle)
        self._idle_timer.start()

    def setup_idle_source(self, provider: Callable[[], float]) -> None:
        """由入口注入"距上次输入活动多少秒"的取数函数。"""
        self._idle_source = provider

    def show_activity(self, kind: str, count: int) -> None:
        self.activity_label.setText(f"最近事件：{kind} · 第 {count} 次")

    def _refresh_idle(self) -> None:
        if self._idle_source is None:
            return
        seconds = int(self._idle_source())
        self.idle_label.setText(
            f"空闲：{seconds} 秒" if seconds < 60 else f"空闲：{seconds // 60} 分 {seconds % 60} 秒"
        )
