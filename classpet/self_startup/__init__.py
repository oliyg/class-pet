"""开机自启动。

设计要点：

- **只有打包后才有可自启动的目标**。开发态跑的是 `uv run run_classpet.py`，写进系统只会让
  开机去执行 python，因此 `is_supported()` 在非打包态一律为 False，界面据此禁用开关。
- **状态的唯一来源是系统本身**（Windows 的 HKCU Run 键），不再另存一份配置。这样安全软件
  把条目清掉时界面会如实反映，不会出现「开关开着但系统里没有」的双份真相。
- 目前只实现 Windows。macOS 要加时新建 `darwin.py`（LaunchAgent + plistlib），
  并在下面的平台分发里接上——没有实机验证前不要写。
"""

import sys

# 自启动命令行参数：入口据此判断"这次启动要静默"，同时它也是写进系统的命令的一部分，
# 两边共用这一个常量，避免改了一处忘了另一处。
AUTOSTART_FLAG = "--autostart"


class SelfStartupError(RuntimeError):
    """设置自启动失败（权限被拒、注册表不可写等）。"""


if sys.platform == "win32":
    from classpet.self_startup import win32 as _impl
else:
    _impl = None


def command() -> str:
    """写进系统的启动命令。exe 路径可能带空格，必须加引号。"""
    return f'"{sys.executable}" {AUTOSTART_FLAG}'


def is_supported() -> bool:
    """能否设置自启动：只有打包后的 Windows。"""
    return _active_impl() is not None


def is_enabled() -> bool:
    """系统里当前是否登记了自启动条目。"""
    return _impl is not None and _impl.read() is not None


def is_stale() -> bool:
    """已启用，但登记的路径不是当前 exe（例如用户把 dist 目录挪走了）。"""
    stored = _impl.read() if _impl is not None else None
    return stored is not None and stored != command()


def enable() -> None:
    """登记自启动（幂等：已有条目则覆盖）。失败抛 SelfStartupError。"""
    impl = _active_impl()
    if impl is None:
        raise SelfStartupError(_unsupported_reason())
    try:
        impl.write(command())
    except OSError as exc:
        raise SelfStartupError(f"写入自启动条目失败：{exc}") from exc


def disable() -> None:
    """取消自启动（幂等：本来没有也算成功）。失败抛 SelfStartupError。"""
    if _impl is None:
        return
    try:
        _impl.remove()
    except OSError as exc:
        raise SelfStartupError(f"删除自启动条目失败：{exc}") from exc


def _active_impl():
    """返回当前可用的平台实现；不支持时返回 None。

    支持条件集中在这里一处判断，避免别处再抄一遍条件而漂移。
    """
    if _impl is None or not getattr(sys, "frozen", False):
        return None
    return _impl


def _unsupported_reason() -> str:
    if _impl is None:
        return f"当前平台（{sys.platform}）暂不支持开机自启动。"
    return "开发态不支持开机自启动，请使用打包后的程序。"
