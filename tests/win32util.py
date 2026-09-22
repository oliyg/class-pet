"""Win32 窗口探针，供进程级测试使用（用 ctypes，不引新依赖）。

非 Windows 上 `ctypes.windll` 根本不存在，所以这里留了运行期守卫；下面所有函数都只在
`skipif(not win32)` 的测试里被调用。
"""

import ctypes
import ctypes.wintypes as wt
import sys
import time

IS_WINDOWS = sys.platform == "win32"
WM_CLOSE = 0x0010
TITLE = "课小宠"  # 窗口标题前缀；设置窗口是「课小宠 ClassPet · 设置」

user32 = ctypes.windll.user32 if IS_WINDOWS else None


def _user32():
    """取 user32；调用方都跑在 Windows 上（断言把 Optional 收窄掉）。"""
    assert user32 is not None, "Win32 探针只能在 Windows 上调用"
    return user32


if IS_WINDOWS:
    # 不写 argtypes 的话句柄会被当 32 位 int 传递，句柄一超过 2^31 就截断。
    _u = _user32()
    _u.EnumWindows.argtypes = [ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM), wt.LPARAM]
    _u.GetWindowTextLengthW.argtypes = [wt.HWND]
    _u.GetWindowTextW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
    _u.IsWindow.argtypes = [wt.HWND]
    _u.IsWindowVisible.argtypes = [wt.HWND]
    _u.PostMessageW.argtypes = [wt.HWND, ctypes.c_uint, wt.WPARAM, wt.LPARAM]


def find_windows(prefix: str = TITLE) -> list[tuple[int, str, bool]]:
    """桌面上标题含 prefix 的窗口：(hwnd, 标题, 是否可见)。隐藏的窗口也在内。"""
    found: list[tuple[int, str, bool]] = []
    u = _user32()

    def callback(hwnd, _lparam):
        length = u.GetWindowTextLengthW(hwnd)
        if length:
            buf = ctypes.create_unicode_buffer(length + 1)
            u.GetWindowTextW(hwnd, buf, length + 1)
            if prefix in buf.value:
                found.append((hwnd, buf.value, bool(u.IsWindowVisible(hwnd))))
        return True

    u.EnumWindows(ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)(callback), 0)
    return found


def wait_for_window(timeout: float, prefix: str = TITLE) -> int | None:
    """等第一个可见的、不是设置页的窗口；等到就返回 hwnd。"""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        for hwnd, title, visible in find_windows(prefix):
            if visible and "· 设置" not in title:
                return hwnd
        time.sleep(0.3)
    return None


def is_window(hwnd: int) -> bool:
    return bool(_user32().IsWindow(hwnd))


def is_visible(hwnd: int) -> bool:
    return bool(_user32().IsWindowVisible(hwnd))


def post_close(hwnd: int) -> None:
    """等价于用户点窗口的 X（走原生路径，不是 Qt 的 close()）。"""
    _user32().PostMessageW(hwnd, WM_CLOSE, 0, 0)
