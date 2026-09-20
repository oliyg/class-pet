"""首页。"""

from PySide6.QtWidgets import QVBoxLayout, QWidget
from qfluentwidgets import BodyLabel, PushButton, SubtitleLabel

from classpet import APP_NAME


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
        title.setText(APP_NAME)
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
