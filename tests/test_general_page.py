"""通用设置页：开关门禁、初始化不误当用户操作。"""


def test_不支持时开关禁用并说明原因(qtbot, settings_window):
    page = settings_window.general

    page.setup_autostart(enabled=False, supported=False)

    assert not page.autostart_card.isEnabled()
    assert "不支持" in page.autostart_hint.text()


def test_登记路径失效时提示重新开启(qtbot, settings_window):
    page = settings_window.general

    page.setup_autostart(enabled=True, supported=True, stale=True)

    assert page.autostart_card.isEnabled()
    assert page.autostart_card.isChecked()  # 初值来自系统真值
    assert "不一致" in page.autostart_hint.text()


def test_初始化不会被当成用户操作(qtbot, settings_window):
    page = settings_window.general

    with qtbot.assertNotEmitted(page.autostart_changed):
        page.setup_autostart(enabled=True, supported=True)


def test_用户拨动开关会发信号(qtbot, settings_window):
    page = settings_window.general
    page.setup_autostart(enabled=False, supported=True)

    with qtbot.waitSignal(page.autostart_changed, timeout=2000) as blocker:
        page.autostart_card.setChecked(True)

    assert blocker.args == [True]
