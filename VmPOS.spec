# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['interface/inicio_sesion.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('database', 'database'),
        ('assets', 'assets'),
        ('interface', 'interface'),
        ('modules', 'modules'),
        ('config', 'config'),
        ('backups', 'backups'),
        ('reports_pdf', 'reports_pdf'),
        ('reports_excel', 'reports_excel'),
    ],
    hiddenimports=['pyttsx3', 'pyttsx3.drivers', 'pyttsx3.drivers.sapi5', 'pyttsx3.drivers.nsss', 'pyttsx3.drivers.espeak', 'reportlab', 'reportlab.lib', 'reportlab.lib.pagesizes', 'reportlab.platypus', 'reportlab.lib.styles', 'reportlab.lib.colors', 'reportlab.lib.units', 'reportlab.pdfbase', 'reportlab.pdfbase.ttfonts', 'reportlab.pdfgen', 'reportlab.pdfgen.canvas', 'matplotlib', 'matplotlib.pyplot', 'matplotlib.backends', 'matplotlib.backends.backend_tkagg', 'matplotlib.dates', 'pandas', 'openpyxl', 'openpyxl.styles', 'PIL', 'PIL.Image', 'PIL.ImageDraw', 'PIL.ImageFont', 'sqlite3', 'tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'tkinter.filedialog', 'tkinter.simpledialog', 'escpos', 'escpos.printer', 'usb', 'usb.core', 'usb.util', 'win32print', 'calendar', 'hashlib', 'base64', 'io', 'threading', 'subprocess', 'tempfile', 'shutil'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='VmPOS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/Salome.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VmPOS',
)
