# -*- mode: python ; coding: utf-8 -*-
# PyInstaller 打包配置。构建：uv run pyinstaller --noconfirm class-pet.spec
# 产物：dist/class-pet/class-pet.exe（onedir，不用 onefile：每次启动解包太慢）

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[("assets/class-pet.ico", "assets")],  # 运行时 app.setWindowIcon 需要它
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
    icon="assets/class-pet.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="class-pet",
)
