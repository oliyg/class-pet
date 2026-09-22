"""进程级契约：关窗不退出，进程常驻托盘。

组件测试只能证明窗口只是收起；这里起**真实进程**（入口脚本 / 打包 exe），从外部用 Win32 断言。
打包版曾经在默认关窗路径上把窗口对象销毁掉——窗口"消失"与"收起"在界面上一样，
只能这样从外部验。
"""

import subprocess
import sys
import time
from pathlib import Path

import pytest
from win32util import find_windows, is_visible, is_window, post_close, wait_for_window

ROOT = Path(__file__).resolve().parents[1]
EXE = ROOT / "dist" / "class-pet" / "class-pet.exe"
win_only = pytest.mark.skipif(not sys.platform.startswith("win"), reason="窗口断言依赖 Win32")


def desktop_has_instance() -> bool:
    """桌面上已有实例时，进程级断言会打在它身上——那样验的是别人的进程。"""
    return bool(find_windows())


@win_only
def test_开发版_关窗后进程仍活着():
    if desktop_has_instance():
        pytest.skip("桌面上已有课小宠在跑，进程级断言会打在它身上")

    proc = subprocess.Popen([sys.executable, str(ROOT / "run_classpet.py")], cwd=str(ROOT))
    try:
        hwnd = wait_for_window(timeout=30)
        assert hwnd is not None, "启动后没等到可见窗口"

        post_close(hwnd)
        time.sleep(2)

        assert is_window(hwnd), "关窗只是收起，窗口对象不该被销毁"
        assert not is_visible(hwnd), "关窗后窗口应当不可见"
        assert proc.poll() is None, "关窗不该结束进程（应常驻托盘）"
    finally:
        proc.terminate()
        proc.wait(timeout=10)


@win_only
def test_打包版_关窗后进程仍活着():
    if not EXE.is_file():
        pytest.skip("还没打包：先跑 uv run pyinstaller --noconfirm class-pet.spec")
    if desktop_has_instance():
        pytest.skip("桌面上已有课小宠在跑，进程级断言会打在它身上")

    proc = subprocess.Popen([str(EXE)], cwd=str(EXE.parent))
    try:
        hwnd = wait_for_window(timeout=60)
        assert hwnd is not None, "启动后没等到可见窗口"

        post_close(hwnd)
        time.sleep(2.5)

        assert is_window(hwnd), "打包版关窗也必须是收起：窗口对象被销毁的话托盘就唤不回来了"
        assert not is_visible(hwnd)
        assert proc.poll() is None, "关窗不该结束进程（应常驻托盘）"
    finally:
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True, check=False
        )
