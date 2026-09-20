"""通用设置页。"""

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QVBoxLayout, QWidget
from qfluentwidgets import BodyLabel, FluentIcon, SubtitleLabel, SwitchSettingCard


class GeneralPage(QWidget):
    """通用设置页。

    页面只表达"用户想改成什么"（`autostart_changed`），真实状态与写系统都由入口负责：
    开关初值用系统真值喂进来，写失败时入口再把它刷回去，避免界面与系统不一致。
    """

    autostart_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        # addSubInterface 要求 objectName 非空，否则抛 ValueError。
        self.setObjectName("generalPage")

        self._loading = False  # 初始化期间不把 setValue 当成用户操作

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)  # 内容区留白，避免控件贴边
        layout.setSpacing(12)  # 相邻控件之间的间距

        title = SubtitleLabel(self)
        title.setText("通用")
        layout.addWidget(title)

        self.autostart_card = SwitchSettingCard(
            FluentIcon.POWER_BUTTON,
            "开机自启动",
            "登录 Windows 后在托盘静默启动，不显示窗口",
            parent=self,
        )
        self.autostart_card.checkedChanged.connect(self._on_autostart_toggled)
        layout.addWidget(self.autostart_card)

        self.autostart_hint = BodyLabel(self)  # 不支持 / 路径失效时说明原因
        layout.addWidget(self.autostart_hint)

        layout.addStretch(1)  # 吸收剩余高度，让控件从上往下排列

    def setup_autostart(self, *, enabled: bool, supported: bool, stale: bool = False) -> None:
        """由入口用系统真值初始化开关。"""
        self._loading = True
        try:
            self.autostart_card.setValue(enabled)
        finally:
            self._loading = False

        self.autostart_card.setEnabled(supported)
        if not supported:
            self.autostart_hint.setText("当前环境不支持：开机自启动只在打包后的程序里可用。")
        elif stale:
            self.autostart_hint.setText("登记的启动路径与当前程序不一致（程序被移动过），请关闭后重新开启。")
        else:
            self.autostart_hint.setText("")

    @Slot(bool)  # 接自己的开关卡片
    def _on_autostart_toggled(self, checked: bool) -> None:
        if not self._loading:  # 初始化时 setValue 也会触发，别误当成用户操作
            self.autostart_changed.emit(checked)
