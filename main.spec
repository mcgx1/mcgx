# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['E:/程序/xiangmu/mcgx/main.py'],
    pathex=[],
    binaries=[],
    datas=[('E:/程序/xiangmu/mcgx/ui', 'ui'), 
           ('E:/程序/xiangmu/mcgx/utils', 'utils'),
           ('E:/程序/xiangmu/mcgx/config', 'config')],
    hiddenimports=['pathlib', 'logging', 'os', 'ui', 'utils', 'config'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['E:/程序/xiangmu/mcgx/fix_imports_hook.py'],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)