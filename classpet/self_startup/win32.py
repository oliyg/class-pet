"""Windows 自启动实现：往 HKCU 的 Run 键写一个字符串值。

只用 HKCU（当前用户），不需要管理员权限；写 HKLM 需要提权，桌面应用不该提权。
"""

import winreg

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_VALUE_NAME = "ClassPet"  # 任务管理器「启动」里显示的名字


def read() -> str | None:
    """读回登记的命令；没有条目时返回 None。"""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as key:
            value, _ = winreg.QueryValueEx(key, _VALUE_NAME)
    except FileNotFoundError:
        return None
    return str(value)


def write(command: str) -> None:
    """写入或覆盖条目（幂等）。键不存在时 CreateKey 会一并创建。"""
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as key:
        winreg.SetValueEx(key, _VALUE_NAME, 0, winreg.REG_SZ, command)


def remove() -> None:
    """删除条目（幂等：本来就没有也算成功）。"""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, _VALUE_NAME)
    except FileNotFoundError:
        pass
