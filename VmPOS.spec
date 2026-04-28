# -*- mode: python ; coding: utf-8 -*-
# Ejecutar desde la raiz del proyecto: pyinstaller VmPOS.spec

from PyInstaller.utils.hooks import collect_data_files

block_cipher = None
escpos_datas = collect_data_files('escpos')

a = Analysis(
    ['interface/inicio_sesion.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('database/license_remote.example.json', 'database'),
        ('assets', 'assets'),
        ('reports_excel', 'reports_excel'),
        ('reports_pdf', 'reports_pdf'),
    ] + escpos_datas,
    hiddenimports=[
        'tkinter', 'sqlite3', 'configparser', 'pathlib', 'traceback',
        'PIL', 'PIL.Image', 'PIL.ImageTk',
        'pandas', 'openpyxl', 'xlsxwriter',
        'reportlab',
        'barcode', 'pyttsx3', 'win32com', 'win32com.client', 'pythoncom',
        'paths',
        'navegacion_ventanas',
        'layout_responsive',
        'menu_inicio', 'pantalla_carga', 'usuarios_db', 'resource_manager',
        'ventas_menu', 'inventario_menu', 'clientes_menu', 'fiado_db', 'fiado_menu',
        'reportes_menu', 'gastos_menu', 'configuracion_menu', 'usuarios_menu',
        'generador_codigo_barras',
        'license_remote',
    ],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='VmPOS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
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
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VmPOS',
)
