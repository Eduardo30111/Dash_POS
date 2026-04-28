# -*- coding: utf-8 -*-
"""Rutas de datos: un solo criterio para desarrollo y ejecutable PyInstaller."""
import os
import shutil
import sys


def is_frozen():
    return bool(getattr(sys, "frozen", False))


def meipass():
    return getattr(sys, "_MEIPASS", None)


def project_root():
    """Carpeta del proyecto o carpeta del .exe (datos persistidos junto al ejecutable)."""
    if is_frozen():
        return os.path.normpath(os.path.dirname(sys.executable))
    interface_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(interface_dir, ".."))


def database_dir():
    d = os.path.join(project_root(), "database")
    os.makedirs(d, exist_ok=True)
    return d


def ventas_db_path():
    return os.path.join(database_dir(), "ventas.db")


def usuarios_db_path():
    return os.path.join(database_dir(), "usuarios.db")


def reports_pdf_dir():
    d = os.path.join(project_root(), "reports_pdf")
    os.makedirs(d, exist_ok=True)
    return d


def reports_excel_dir():
    d = os.path.join(project_root(), "reports_excel")
    os.makedirs(d, exist_ok=True)
    return d


def backups_dir():
    d = os.path.join(project_root(), "backups")
    os.makedirs(d, exist_ok=True)
    return d


def license_remote_config_path():
    """JSON de control remoto de licencia (junto a ventas.db en database/)."""
    return os.path.join(database_dir(), "license_remote.json")


def _bundle_file(rel):
    m = meipass()
    if not m:
        return None
    p = os.path.normpath(os.path.join(m, rel))
    return p if os.path.isfile(p) else None


def ensure_runtime_databases():
    """
    En el .exe, copia las BDs iniciales desde el bundle a database/ junto al ejecutable
    si aún no existen (escritura persistente).
    """
    if not is_frozen():
        return
    ddir = database_dir()
    for name in ("ventas.db", "usuarios.db"):
        dest = os.path.join(ddir, name)
        if os.path.exists(dest):
            continue
        src = _bundle_file(f"database/{name}")
        if src:
            try:
                shutil.copy2(src, dest)
            except OSError as e:
                print(f"VmPOS: no se pudo copiar {name} desde el bundle: {e}")
    # Config remota de licencia: crear archivo editable local al primer inicio.
    lic_dest = os.path.join(ddir, "license_remote.json")
    if not os.path.exists(lic_dest):
        lic_src = _bundle_file("database/license_remote.example.json")
        if lic_src:
            try:
                shutil.copy2(lic_src, lic_dest)
            except OSError as e:
                print(f"VmPOS: no se pudo copiar license_remote.json inicial: {e}")


def assets_dir():
    """Recursos gráficos: en bundle bajo _MEIPASS; en dev en la raíz del proyecto."""
    m = meipass()
    if m:
        p = os.path.join(m, "assets")
        if os.path.isdir(p):
            return p
    return os.path.join(project_root(), "assets")
