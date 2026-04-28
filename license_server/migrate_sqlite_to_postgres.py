#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migra licencias desde SQLite local a PostgreSQL (Render).

Uso:
  set DATABASE_URL=postgresql://...
  python migrate_sqlite_to_postgres.py

Opcional:
  set SQLITE_PATH=./data/licenses.sqlite
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import psycopg


def _sqlite_path() -> Path:
    raw = (os.environ.get("SQLITE_PATH") or "").strip()
    if raw:
        return Path(raw).resolve()
    return (Path(__file__).resolve().parent / "data" / "licenses.sqlite").resolve()


def _pg_url() -> str:
    url = (os.environ.get("DATABASE_URL") or "").strip()
    if not url:
        raise RuntimeError("Falta DATABASE_URL en variables de entorno.")
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://") :]
    return url


def main() -> None:
    sqlite_path = _sqlite_path()
    if not sqlite_path.exists():
        raise RuntimeError(f"No existe SQLite origen: {sqlite_path}")

    src = sqlite3.connect(str(sqlite_path))
    src.row_factory = sqlite3.Row
    cur = src.cursor()
    cur.execute(
        """
        SELECT license_key, label, is_active, updated_at, last_client_check, period_start, period_end
        FROM licenses
        ORDER BY license_key
        """
    )
    rows = cur.fetchall()

    if not rows:
        print("No hay filas en SQLite para migrar.")
        return

    with psycopg.connect(_pg_url()) as conn:
        with conn.cursor() as c:
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS licenses (
                    license_key TEXT PRIMARY KEY,
                    label TEXT,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    updated_at TEXT,
                    last_client_check TEXT,
                    period_start TEXT,
                    period_end TEXT
                )
                """
            )
            for r in rows:
                c.execute(
                    """
                    INSERT INTO licenses
                        (license_key, label, is_active, updated_at, last_client_check, period_start, period_end)
                    VALUES
                        (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT(license_key) DO UPDATE SET
                        label=excluded.label,
                        is_active=excluded.is_active,
                        updated_at=excluded.updated_at,
                        last_client_check=excluded.last_client_check,
                        period_start=excluded.period_start,
                        period_end=excluded.period_end
                    """,
                    (
                        r["license_key"],
                        r["label"],
                        int(r["is_active"] or 0),
                        r["updated_at"],
                        r["last_client_check"],
                        r["period_start"],
                        r["period_end"],
                    ),
                )
        conn.commit()

    print(f"Migracion completa: {len(rows)} licencias -> PostgreSQL.")


if __name__ == "__main__":
    main()

