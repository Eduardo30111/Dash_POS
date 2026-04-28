#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recursos y rutas para PyInstaller (compatibilidad con código que importe este módulo).
La lógica principal vive en paths.py.
"""

import os
import sys

from paths import (
    assets_dir,
    backups_dir,
    database_dir,
    ensure_runtime_databases,
    project_root,
    reports_excel_dir,
    reports_pdf_dir,
    usuarios_db_path,
    ventas_db_path,
)


def get_resource_path(relative_path):
    """
    Ruta a un archivo empaquetado (lectura) o bajo la raíz del proyecto en desarrollo.
    """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = project_root()
    return os.path.join(base_path, relative_path)


def get_database_path():
    """Ruta al bundle de ventas.db (origen de copia); datos de trabajo: ventas_db_path()."""
    return get_resource_path(os.path.join("database", "ventas.db"))


def get_users_database_path():
    return get_resource_path(os.path.join("database", "usuarios.db"))


def get_assets_path():
    return assets_dir()


def get_reports_path():
    return reports_pdf_dir()


def get_excel_reports_path():
    return reports_excel_dir()


def get_backups_path():
    return backups_dir()


def ensure_directories_exist():
    """Crea directorios de datos bajo project_root (persistente)."""
    for fn in (database_dir, reports_pdf_dir, reports_excel_dir, backups_dir):
        fn()
    config_d = os.path.join(project_root(), "config")
    try:
        os.makedirs(config_d, exist_ok=True)
    except OSError as e:
        print(f"Error creando {config_d}: {e}")


def is_compiled():
    return bool(getattr(sys, "frozen", False))


def get_app_directory():
    return project_root()


def copy_database_to_app_dir():
    """Delegado en la copia inicial definida en paths.ensure_runtime_databases."""
    ensure_runtime_databases()


if __name__ == "__main__":
    print("Inicializando gestor de recursos...")
    ensure_directories_exist()
    if is_compiled():
        copy_database_to_app_dir()
    print("Listo. ventas (trabajo):", ventas_db_path())
