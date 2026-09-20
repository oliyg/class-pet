"""课小宠 ClassPet 入口：创建对象、连接跨模块信号、启动事件循环。

业务实现都在 classpet/ 包里，本文件只做编排。
"""

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox
from qfluentwidgets import Theme, setTheme
from tendo import singleton

from classpet import APP_NAME
from classpet.dashboard.main_window import MainWindow
from classpet.modules import InputMonitor, SchedulerWorker
from classpet.notification import NotificationService
from classpet.utils import resource_path


def report_already_running() -> None:
    """告知用户已有实例在运行。

    打包后（`sys.frozen`）进程没有控制台，往 stderr 写等于石沉大海，必须弹对话框；
    开发时保持只写 stderr，方便脚本与终端观察。
    """
    if not getattr(sys, "frozen", False):
        print(f"{APP_NAME} 已在运行，本次启动退出。", file=sys.stderr)
        return

    _app = QApplication(sys.argv)  # QMessageBox 需要先有 QApplication，引用要保留以免被回收
    QMessageBox.information(None, APP_NAME, "课小宠已在运行，请勿重复启动。")


def main() -> int:
    # 单实例：锁文件放在系统临时目录，第二个实例会抛 SingleInstanceException。
    # 必须留住 instance 这个引用——对象一旦被回收，__del__ 会立刻删掉锁文件，单实例随即失效。
    try:
        instance = singleton.SingleInstance("class-pet")  # noqa: F841 —— 见上：这个引用不能删
    except singleton.SingleInstanceException:
        # 已有实例在运行：不用再启动 Qt 主流程，直接退出。
        report_already_running()
        return 1

    # 高 DPI 缩放策略必须在 QApplication 构造之前设置，否则不生效。
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("icons", "class-pet.ico")))  # 任务栏 / Alt-Tab 图标
    setTheme(Theme.AUTO)  # 主题跟随系统明暗

    # 后台模块与界面在此创建，并在下面的连线区集中挂钩。它们必须一直被引用着，
    # 所以都留在这个函数的局部作用域里（main() 一直活到 app.exec() 返回）。
    window = MainWindow()
    monitor = InputMonitor()
    scheduler = SchedulerWorker()
    notification = NotificationService()

    # 跨模块连线集中在这里，模块之间不互相 import。
    window.setup_activity(monitor)  # 输入活动 → 首页状态行
    scheduler.reminder_due.connect(notification.show)  # 到点提醒 → 系统通知

    window.show()  # 先显示窗口，再进入事件循环
    monitor.start()  # 窗口就绪后再挂全局钩子
    scheduler.start()  # 依附 Qt 事件循环，必须在 app.exec() 之前启动
    app.aboutToQuit.connect(monitor.stop)  # 退出前务必摘下钩子
    app.aboutToQuit.connect(scheduler.shutdown)

    return app.exec()  # 阻塞至窗口关闭，返回进程退出码


if __name__ == "__main__":
    sys.exit(main())
