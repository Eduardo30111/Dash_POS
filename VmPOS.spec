# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['interface\\inicio_sesion.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets'), ('database', 'database')],
    hiddenimports=['escpos.printer', 'escpos', 'usb', 'pywin32', 'win32print', 'matplotlib', 'matplotlib.backends', 'reportlab', 'openpyxl', 'pandas'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
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
    name='VmPOS',
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
    icon=['assets\\salome.ico'],
)
