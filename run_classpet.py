"""课小宠 ClassPet 入口：创建对象、连接跨模块信号、启动事件循环。

业务实现都在 classpet/ 包里，本文件只做编排。
"""

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox
from qfluentwidgets import Theme, setTheme
from tendo import singleton

from classpet import APP_NAME, self_startup
from classpet.dashboard.window import DashboardWindow
from classpet.input_monitor import InputMonitor
from classpet.notification import NotificationService
from classpet.scheduler_worker import SchedulerWorker
from classpet.settings.window import SettingsWindow
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
    dashboard = DashboardWindow()
    settings = SettingsWindow()
    monitor = InputMonitor()
    scheduler = SchedulerWorker()
    notification = NotificationService()

    def apply_autostart(enabled: bool) -> None:
        """把设置页的意图写进系统。

        失败（例如被安全软件拦截）就弹窗说明，然后**无论成败都以系统真值刷新界面**——
        绝不让开关停在一个没生效的位置上。
        """
        try:
            if enabled:
                self_startup.enable()
            else:
                self_startup.disable()
        except self_startup.SelfStartupError as exc:
            QMessageBox.warning(None, APP_NAME, str(exc))

        settings.setup_autostart(
            enabled=self_startup.is_enabled(),
            supported=self_startup.is_supported(),
            stale=self_startup.is_stale(),
        )

    # 跨模块连线集中在这里，模块之间不互相 import。
    dashboard.setup_activity(monitor)  # 输入活动 → 状态页
    settings.setup_autostart(  # 开关初值 = 系统里的真值
        enabled=self_startup.is_enabled(),
        supported=self_startup.is_supported(),
        stale=self_startup.is_stale(),
    )
    settings.autostart_changed.connect(apply_autostart)  # 开关 → 写系统
    scheduler.reminder_due.connect(notification.show)  # 到点提醒 → 系统通知
    notification.dashboard_requested.connect(dashboard.show_and_raise)  # 托盘 → 控制台
    notification.settings_requested.connect(settings.show_and_raise)  # 托盘 → 设置
    notification.quit_requested.connect(app.quit)  # 托盘菜单 → 退出

    # 开机自启（--autostart）时两个窗口都不显示，只驻留托盘。
    if self_startup.AUTOSTART_FLAG not in sys.argv:
        dashboard.show()
    monitor.start()  # 全局钩子
    scheduler.start()  # 依附 Qt 事件循环，必须在 app.exec() 之前启动
    app.aboutToQuit.connect(monitor.stop)  # 退出前务必摘下钩子
    app.aboutToQuit.connect(scheduler.shutdown)

    return app.exec()  # 阻塞至窗口关闭（或托盘菜单退出），返回进程退出码


if __name__ == "__main__":
    sys.exit(main())
