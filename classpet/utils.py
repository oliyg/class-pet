"""通用工具。"""

import os
import sys


def resource_path(*parts: str) -> str:
    """定位 res/ 下的资源。

    开发时是仓库根目录下的 res/，PyInstaller 打包后在 sys._MEIPASS/res/。
    """
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, "res", *parts)
