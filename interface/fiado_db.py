# -*- coding: utf-8 -*-
"""Esquema y lógica de fiados: ventas a crédito por documento y abonos."""
import sqlite3
from datetime import datetime

from paths import ventas_db_path


def _ensure_clientes_tabla(c):
    """Ficha nombre/cédula compartida con el módulo Clientes (misma BD ventas.db)."""
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clientes'")
    if not c.fetchone():
        c.execute(
            """
            CREATE TABLE clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cedula TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                email TEXT,
                telefono TEXT,
                fecha_registro TEXT NOT NULL
            )
            """
        )


def ensure_fiado_schema(conn):
    """Asegura tablas y columnas para fiados (abonos, tipo_pago en ventas y registro_clientes)."""
    c = conn.cursor()
    _ensure_clientes_tabla(c)
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS abonos_fiado (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            documento_cliente TEXT NOT NULL,
            monto REAL NOT NULL,
            fecha TEXT NOT NULL,
            hora TEXT NOT NULL,
            nota TEXT
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS registro_clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            documento TEXT,
            fecha_compra TEXT,
            hora_compra TEXT,
            total_compras REAL
        )
        """
    )
    for col, decl in [
        ("hora_compra", "TEXT"),
        ("tipo_pago", "TEXT DEFAULT 'contado'"),
        ("id_venta", "INTEGER"),
    ]:
        try:
            c.execute(f"ALTER TABLE registro_clientes ADD COLUMN {col} {decl}")
        except sqlite3.OperationalError:
            pass
    for col, decl in [("tipo_pago", "TEXT DEFAULT 'contado'")]:
        try:
            c.execute(f"ALTER TABLE ventas ADD COLUMN {col} {decl}")
        except sqlite3.OperationalError:
            pass
    stock_col_nueva = False
    try:
        c.execute("ALTER TABLE ventas ADD COLUMN stock_aplicado INTEGER")
        stock_col_nueva = True
    except sqlite3.OperationalError:
        pass
    # Solo la primera vez que existe la columna: fiados viejos ya habían descontado stock al vender.
    if stock_col_nueva:
        c.execute(
            """
            UPDATE ventas SET stock_aplicado = 1
            WHERE COALESCE(LOWER(tipo_pago), 'contado') = 'fiado'
              AND stock_aplicado IS NULL
            """
        )
    conn.commit()


def ensure_fiado_schema_file():
    if not _db_exists():
        return
    with sqlite3.connect(ventas_db_path()) as conn:
        ensure_fiado_schema(conn)


def _db_exists():
    import os
    return os.path.exists(ventas_db_path())


def saldo_pendiente(documento: str) -> float:
    """Suma de ventas en fiado menos abonos registrados para el documento."""
    doc = (documento or "").strip()
    if not doc or not _db_exists():
        return 0.0
    with sqlite3.connect(ventas_db_path()) as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT COALESCE(SUM(total_venta), 0)
            FROM ventas
            WHERE documento_cliente = ? AND COALESCE(LOWER(tipo_pago), 'contado') = 'fiado'
            """,
            (doc,),
        )
        total_fiado = float(c.fetchone()[0] or 0)
        c.execute(
            "SELECT COALESCE(SUM(monto), 0) FROM abonos_fiado WHERE documento_cliente = ?",
            (doc,),
        )
        abonos = float(c.fetchone()[0] or 0)
    return max(0.0, total_fiado - abonos)


def aplicar_stock_al_saldar_fiado(documento: str) -> None:
    """
    Si la deuda del documento quedó en cero, descuenta inventario de las ventas
    a fiado de ese documento que aún no tenían stock aplicado (stock_aplicado = 0).
    """
    doc = (documento or "").strip()
    if not doc or not _db_exists():
        return
    if saldo_pendiente(doc) > 0.009:
        return
    with sqlite3.connect(ventas_db_path()) as conn:
        ensure_fiado_schema(conn)
        c = conn.cursor()
        c.execute("PRAGMA table_info(ventas)")
        if "stock_aplicado" not in [x[1] for x in c.fetchall()]:
            return
        c.execute(
            """
            SELECT id FROM ventas
            WHERE documento_cliente = ?
              AND COALESCE(LOWER(tipo_pago), 'contado') = 'fiado'
              AND COALESCE(stock_aplicado, -1) = 0
            """,
            (doc,),
        )
        ids = [r[0] for r in c.fetchall()]
        for id_venta in ids:
            c.execute(
                """
                SELECT codigo_producto, cantidad
                FROM detalle_ventas
                WHERE id_venta = ?
                """,
                (id_venta,),
            )
            for codigo, cantidad in c.fetchall():
                if not codigo or codigo == "N/A":
                    continue
                try:
                    c.execute(
                        "SELECT COALESCE(tipo, 'producto') FROM productos WHERE codigo = ?",
                        (codigo,),
                    )
                    tr = c.fetchone()
                except sqlite3.OperationalError:
                    tr = None
                t_item = (tr[0] or "producto").lower() if tr else "producto"
                if t_item == "servicio":
                    continue
                c.execute(
                    "UPDATE productos SET stock = stock - ? WHERE codigo = ?",
                    (int(cantidad or 0), codigo),
                )
            c.execute(
                "UPDATE ventas SET stock_aplicado = 1 WHERE id = ?",
                (id_venta,),
            )
        conn.commit()


def registrar_abono(documento: str, monto: float, nota: str = "") -> bool:
    doc = (documento or "").strip()
    if not doc or monto is None or monto <= 0:
        return False
    ensure_fiado_schema_file()
    ahora = datetime.now()
    with sqlite3.connect(ventas_db_path()) as conn:
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO abonos_fiado (documento_cliente, monto, fecha, hora, nota)
            VALUES (?, ?, ?, ?, ?)
            """,
            (doc, float(monto), ahora.strftime("%Y-%m-%d"), ahora.strftime("%H:%M:%S"), (nota or "").strip() or None),
        )
        conn.commit()
    try:
        if saldo_pendiente(doc) <= 0.009:
            aplicar_stock_al_saldar_fiado(doc)
    except Exception:
        pass
    return True


def listar_abonos(documento: str, limite: int = 200):
    doc = (documento or "").strip()
    if not doc or not _db_exists():
        return []
    with sqlite3.connect(ventas_db_path()) as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT fecha, hora, monto, nota
            FROM abonos_fiado
            WHERE documento_cliente = ?
            ORDER BY fecha DESC, hora DESC
            LIMIT ?
            """,
            (doc, limite),
        )
        return c.fetchall()


def upsert_cliente_por_cedula(cedula: str, nombre: str | None = None) -> None:
    """
    Crea o conserva ficha en ``clientes`` para una cédula (p. ej. tras una venta fiado).
    Si ya existe, no sobrescribe el nombre salvo que se pase ``nombre`` no vacío.
    """
    ced = (cedula or "").strip()
    if not ced or not _db_exists():
        return
    ensure_fiado_schema_file()
    nom = (nombre or "").strip() or f"Cliente {ced}"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(ventas_db_path()) as conn:
        c = conn.cursor()
        _ensure_clientes_tabla(c)
        c.execute("SELECT id, nombre FROM clientes WHERE cedula = ?", (ced,))
        row = c.fetchone()
        if row:
            if (nombre or "").strip():
                c.execute(
                    "UPDATE clientes SET nombre = ?, fecha_registro = ? WHERE cedula = ?",
                    ((nombre or "").strip(), now, ced),
                )
        else:
            c.execute(
                """
                INSERT INTO clientes (cedula, nombre, email, telefono, fecha_registro)
                VALUES (?, ?, '', '', ?)
                """,
                (ced, nom, now),
            )
        conn.commit()


def nombre_para_documento(documento: str) -> str:
    doc = (documento or "").strip()
    if not doc or not _db_exists():
        return ""
    with sqlite3.connect(ventas_db_path()) as conn:
        c = conn.cursor()
        c.execute("SELECT nombre FROM clientes WHERE cedula = ?", (doc,))
        r = c.fetchone()
        return (r[0] or "").strip() if r else ""


def listar_documentos_fiado_distintos() -> list[str]:
    """Cédulas/documentos que aparecen en ventas fiado o en abonos."""
    if not _db_exists():
        return []
    with sqlite3.connect(ventas_db_path()) as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT documento_cliente FROM ventas
            WHERE COALESCE(LOWER(tipo_pago), 'contado') = 'fiado'
              AND TRIM(COALESCE(documento_cliente,'')) != ''
            UNION
            SELECT documento_cliente FROM abonos_fiado
            WHERE TRIM(COALESCE(documento_cliente,'')) != ''
            """
        )
        seen = []
        for (d,) in c.fetchall():
            x = (d or "").strip()
            if x and x not in seen:
                seen.append(x)
        c.execute("SELECT cedula FROM clientes WHERE TRIM(COALESCE(cedula,'')) != ''")
        for (d,) in c.fetchall():
            x = (d or "").strip()
            if x and x not in seen:
                seen.append(x)
        return sorted(seen, key=lambda s: s.lower())


def listar_perfiles_fiado() -> list[tuple[str, str, float]]:
    """Lista (cedula, nombre, deuda_pendiente) para el panel de cuentas."""
    out: list[tuple[str, str, float]] = []
    for doc in listar_documentos_fiado_distintos():
        nom = nombre_para_documento(doc) or "—"
        deuda = saldo_pendiente(doc)
        out.append((doc, nom, deuda))
    out.sort(key=lambda t: (-t[2], t[0].lower()))
    return out


def actualizar_nombre_cliente(cedula: str, nombre: str) -> tuple[bool, str]:
    ced = (cedula or "").strip()
    nom = (nombre or "").strip()
    if not ced:
        return False, "La cédula no puede estar vacía."
    if not nom:
        return False, "El nombre no puede estar vacío."
    ensure_fiado_schema_file()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(ventas_db_path()) as conn:
        c = conn.cursor()
        _ensure_clientes_tabla(c)
        c.execute("SELECT id FROM clientes WHERE cedula = ?", (ced,))
        if c.fetchone():
            c.execute(
                "UPDATE clientes SET nombre = ?, fecha_registro = ? WHERE cedula = ?",
                (nom, now, ced),
            )
        else:
            c.execute(
                "INSERT INTO clientes (cedula, nombre, email, telefono, fecha_registro) VALUES (?,?,?,?,?)",
                (ced, nom, "", "", now),
            )
        conn.commit()
    return True, ""


def cambiar_cedula_cliente_fiado(cedula_vieja: str, cedula_nueva: str) -> tuple[bool, str]:
    """
    Renombra la cédula en ventas fiado y abonos, y en ``clientes``.
    No modifica montos; solo referencias.
    """
    v = (cedula_vieja or "").strip()
    n = (cedula_nueva or "").strip()
    if not v or not n:
        return False, "Ambas cédulas son obligatorias."
    if v == n:
        return True, ""
    ensure_fiado_schema_file()
    try:
        with sqlite3.connect(ventas_db_path()) as conn:
            c = conn.cursor()
            _ensure_clientes_tabla(c)
            c.execute(
                """
                SELECT 1 FROM ventas
                WHERE documento_cliente = ? AND COALESCE(LOWER(tipo_pago), 'contado') = 'fiado'
                LIMIT 1
                """,
                (n,),
            )
            if c.fetchone():
                return False, "Ya existen ventas a fiado con la cédula nueva. Use otra cédula o fusione datos manualmente."
            c.execute("SELECT 1 FROM abonos_fiado WHERE documento_cliente = ? LIMIT 1", (n,))
            if c.fetchone():
                return False, "Ya existen abonos con la cédula nueva."
            c.execute(
                """
                UPDATE ventas SET documento_cliente = ?
                WHERE documento_cliente = ? AND COALESCE(LOWER(tipo_pago), 'contado') = 'fiado'
                """,
                (n, v),
            )
            c.execute(
                "UPDATE abonos_fiado SET documento_cliente = ? WHERE documento_cliente = ?",
                (n, v),
            )
            c.execute("SELECT id FROM clientes WHERE cedula = ?", (v,))
            row_old = c.fetchone()
            c.execute("SELECT id FROM clientes WHERE cedula = ?", (n,))
            row_new = c.fetchone()
            if row_old and row_new:
                c.execute("DELETE FROM clientes WHERE cedula = ?", (v,))
            elif row_old:
                c.execute("UPDATE clientes SET cedula = ? WHERE cedula = ?", (n, v))
            elif not row_old and not row_new:
                pass
            conn.commit()
    except sqlite3.IntegrityError as e:
        return False, f"No se pudo cambiar la cédula (¿duplicada?): {e}"
    return True, ""


def listar_ventas_fiado(documento: str, limite: int = 200):
    doc = (documento or "").strip()
    if not doc or not _db_exists():
        return []
    with sqlite3.connect(ventas_db_path()) as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT id, fecha_venta, hora_venta, total_venta
            FROM ventas
            WHERE documento_cliente = ? AND COALESCE(LOWER(tipo_pago), 'contado') = 'fiado'
            ORDER BY fecha_venta DESC, hora_venta DESC
            LIMIT ?
            """,
            (doc, limite),
        )
        return c.fetchall()
