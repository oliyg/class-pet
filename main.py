# 课小宠 ClassPet —— 单体单文件应用，全部逻辑都写在本文件内。
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget

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

        layout.addStretch(1)  # 吸收剩余高度，让控件从上往下排列


class MainWindow(FluentWindow):
    """主窗口：左侧导航栏 + 右侧内容区。"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("课小宠 ClassPet")
        self.resize(640, 420)  # 初始窗口尺寸

        # 保留为属性，便于后续切页或访问该页面。
        self.home_page = HomePage(self)
        self.addSubInterface(self.home_page, FluentIcon.HOME, "首页")  # 注册进导航栏


def main() -> int:
    # 高 DPI 缩放策略必须在 QApplication 构造之前设置，否则不生效。
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    setTheme(Theme.AUTO)  # 主题跟随系统明暗

    window = MainWindow()
    window.show()  # 先显示窗口，再进入事件循环
    return app.exec()  # 阻塞至窗口关闭，返回进程退出码


if __name__ == "__main__":
    sys.exit(main())
