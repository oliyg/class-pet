"""主窗口：左侧导航栏 + 右侧内容区。"""

from qfluentwidgets import FluentIcon, FluentWindow

from classpet import APP_NAME
from classpet.dashboard.home import HomePage
from classpet.modules import InputMonitor


class MainWindow(FluentWindow):
    """主窗口。

    只负责界面装配；后台模块由入口创建后经 `setup_*` 挂进来，
    这样界面层不必知道 worker 从哪来，模块之间也不互相 import。
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(640, 420)  # 初始窗口尺寸

        self.home = HomePage(self)
        self.addSubInterface(self.home, FluentIcon.HOME, "首页")  # 注册进导航栏

    def setup_activity(self, monitor: InputMonitor) -> None:
        """把全局输入监听接到首页状态行。"""
        monitor.activity.connect(self.home.show_activity)
