# -*- mode: python ; coding: utf-8 -*-
# PyInstaller 打包配置。构建：uv run pyinstaller --noconfirm class-pet.spec
# 产物：dist/class-pet/class-pet.exe（onedir，不用 onefile：每次启动解包太慢）
#
# Analysis / PYZ / EXE / COLLECT 平时由 PyInstaller 注入到 spec 的全局命名空间
# （见 PyInstaller/building/build_main.py 的 spec_namespace 与 exec(code, spec_namespace)），
# 文件里不声明，静态检查器就会报 "Analysis" is not defined。这里显式 import 的是同一批
# 对象，PyInstaller 执行时只会用同样的值覆盖一次，无运行时副作用。
from PyInstaller.building.api import COLLECT, EXE, PYZ
from PyInstaller.building.build_main import Analysis

a = Analysis(
    ["run_classpet.py"],
    pathex=[],
    binaries=[],
    datas=[("res/icons/class-pet.ico", "res/icons")],  # 运行时 setWindowIcon 需要它
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="class-pet",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # GUI 程序，不弹控制台窗口
    disable_windowed_traceback=False,
    icon="res/icons/class-pet.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="class-pet",
)
