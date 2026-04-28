import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
from collections import defaultdict
from datetime import datetime, timedelta
import calendar
from layout_responsive import (
    bind_reflow_grid_uniform,
    bind_reflow_pack,
    centrar_ventana,
    crear_cuerpo_modulo_scroll,
    modulo_scroll_finalizar,
)
from ui_theme import T, F_TITLE, F_HEAD, F_SUB, F_BODY, F_BODY_B, F_SMALL, F_STAT, style_ttk_treeview_pos
def verificar_y_crear_tablas():
    """Verifica que todas las tablas necesarias existan y las crea si es necesario."""
    global conn, cursor
    if not conn or not cursor:
        if not conectar_db():
            return False
    
    try:
        # Verificar si existe la tabla ventas
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='ventas'
        """)
        tabla_ventas = cursor.fetchone()
        
        
        # Verificar si existe la tabla detalle_ventas
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='detalle_ventas'
        """)
        tabla_detalle = cursor.fetchone()
        
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"❌ Error verificando/creando tablas: {e}")
        if conn:
            conn.rollback()
        return False

# Importaciones opcionales con manejo de errores
try:
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_DISPONIBLE = True
except ImportError as e:
    print(f"Warning: ReportLab no disponible: {e}")
    REPORTLAB_DISPONIBLE = False

try:
    import pandas as pd
    PANDAS_DISPONIBLE = True
except ImportError as e:
    print(f"Warning: Pandas no disponible: {e}")
    PANDAS_DISPONIBLE = False

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    OPENPYXL_DISPONIBLE = True
except ImportError as e:
    print(f"Warning: OpenPyXL no disponible: {e}")
    OPENPYXL_DISPONIBLE = False

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import matplotlib.dates as mdates
    MATPLOTLIB_DISPONIBLE = True
except ImportError as e:
    print(f"Warning: Matplotlib no disponible: {e}")
    MATPLOTLIB_DISPONIBLE = False

from paths import ventas_db_path, reports_pdf_dir, reports_excel_dir

ruta_db = ventas_db_path()
database_dir = os.path.dirname(ruta_db)
pdf_dir = reports_pdf_dir()
excel_dir = reports_excel_dir()

# 🔌 Single database connection
conn = None
cursor = None

def conectar_db():
    """Establishes a single connection to the database."""
    global conn, cursor
    try:
        # Asegurar que el directorio existe
        os.makedirs(os.path.dirname(ruta_db), exist_ok=True)
        
        conn = sqlite3.connect(ruta_db)
        cursor = conn.cursor()
        
        # Verificar y crear tablas necesarias
        verificar_y_crear_tablas()
        crear_tabla_gastos_si_no_existe()
        
        return True
    except Exception as e:
        messagebox.showerror("Error de conexión", f"No se pudo conectar a la base de datos:\n{e}")
        return False

def crear_tabla_gastos_si_no_existe():
    """Crea la tabla de gastos si no existe."""
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gastos (
                id_gasto INTEGER PRIMARY KEY AUTOINCREMENT,
                concepto TEXT NOT NULL,
                valor REAL NOT NULL,
                fecha TEXT NOT NULL,
                hora TEXT NOT NULL,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    except Exception as e:
        messagebox.showerror("Error de base de datos", f"Error al crear la tabla 'gastos': {e}")
        conn.rollback()

def cerrar_app(ventana):
    """Closes the database connection and the main window."""
    if conn:
        conn.close()
    ventana.destroy()

def formato_peso(valor):
    """Formats a numeric value to the Colombian peso representation."""
    return f"${valor:,.0f} COP"


def _ttk_tree_theme(root_widget):
    s = ttk.Style(root_widget)
    style_ttk_treeview_pos(s, T.BG_APP)


def limpiar_precio(texto):
    """Cleans a text string to extract a numeric float value."""
    texto = texto.replace("$", "").replace("COP", "").replace(",", "").strip()
    try:
        return float(texto)
    except ValueError:
        return 0.0

def convertir_fecha_sql(fecha_dd_mm_yyyy):
    """Convierte fecha de formato DD-MM-YYYY a YYYY-MM-DD para SQL."""
    try:
        fecha_obj = datetime.strptime(fecha_dd_mm_yyyy, "%d-%m-%Y")
        return fecha_obj.strftime("%Y-%m-%d")
    except (ValueError, TypeError, AttributeError):
        return fecha_dd_mm_yyyy

def obtener_gastos_periodo(fecha_inicio, fecha_fin):
    """Obtiene los gastos de un período específico."""
    try:
        # Convertir fechas si están en formato DD-MM-YYYY
        if len(fecha_inicio.split('-')[0]) == 2:  # Si el día tiene 2 dígitos, está en formato DD-MM-YYYY
            fecha_inicio_sql = convertir_fecha_sql(fecha_inicio)
            fecha_fin_sql = convertir_fecha_sql(fecha_fin)
        else:
            fecha_inicio_sql = fecha_inicio
            fecha_fin_sql = fecha_fin
            
        cursor.execute("""
            SELECT concepto, valor, fecha, hora FROM gastos
            WHERE date(substr(fecha, 7, 4) || '-' || 
                      case when length(substr(fecha, 4, 2)) = 1 then '0' || substr(fecha, 4, 2) else substr(fecha, 4, 2) end || '-' ||
                      case when length(substr(fecha, 1, 2)) = 1 then '0' || substr(fecha, 1, 2) else substr(fecha, 1, 2) end)
                  BETWEEN date(?) AND date(?)
            ORDER BY fecha_registro DESC
        """, (fecha_inicio_sql, fecha_fin_sql))
        return cursor.fetchall()
    except Exception as e:
        messagebox.showerror("Error", f"Error al obtener gastos del período: {e}")
        return []

def crear_tabla_reportes_si_no_existe():
    """Crea la tabla 'reportes' si no existe."""
    if not conectar_db(): return
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reportes (
                id_reporte INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                fecha_inicio TEXT NOT NULL,
                fecha_fin TEXT NOT NULL,
                resumen TEXT,
                ruta_pdf TEXT
            )
        """)
        conn.commit()
    except Exception as e:
        messagebox.showerror("Error de base de datos", f"Error al crear la tabla 'reportes': {e}")
        conn.rollback()


def _recolectar_reporte_financiero_mes(fecha_inicio_str: str, fecha_fin_str: str):
    """
    Totales desde ``ventas`` y ``gastos``, líneas de venta (detalle si existe),
    ventas agrupadas por día, gastos ordenados cronológicos.
    """
    if not cursor:
        return {
            "total_ventas": 0.0,
            "total_gastos": 0.0,
            "ganancia_neta": 0.0,
            "ventas_por_dia": [],
            "ventas_lineas": [],
            "gastos": [],
            "suma_lineas_subtotal": None,
        }

    cursor.execute(
        """
        SELECT COALESCE(SUM(total_venta), 0) FROM ventas
        WHERE fecha_venta BETWEEN ? AND ?
        """,
        (fecha_inicio_str, fecha_fin_str),
    )
    total_ventas = float(cursor.fetchone()[0] or 0)

    cursor.execute(
        """
        SELECT fecha_venta, COALESCE(SUM(total_venta), 0) AS dia_total
        FROM ventas
        WHERE fecha_venta BETWEEN ? AND ?
        GROUP BY fecha_venta
        ORDER BY fecha_venta ASC
        """,
        (fecha_inicio_str, fecha_fin_str),
    )
    ventas_por_dia = [(r[0], float(r[1])) for r in cursor.fetchall()]

    cursor.execute(
        """
        SELECT name FROM sqlite_master WHERE type='table' AND name IN ('ventas', 'detalle_ventas')
        """
    )
    tablas = {r[0] for r in cursor.fetchall()}

    ventas_lineas = []
    if "ventas" not in tablas:
        pass
    elif "detalle_ventas" not in tablas:
        cursor.execute(
            """
            SELECT fecha_venta, hora_venta, 'Venta general', 1, total_venta, total_venta
            FROM ventas
            WHERE fecha_venta BETWEEN ? AND ?
            ORDER BY fecha_venta ASC, hora_venta ASC
            """,
            (fecha_inicio_str, fecha_fin_str),
        )
        ventas_lineas = [tuple(row) for row in cursor.fetchall()]
    else:
        cursor.execute(
            """
            SELECT v.fecha_venta, v.hora_venta,
                   COALESCE(dv.nombre_producto, 'Venta general'),
                   COALESCE(dv.cantidad, 1),
                   COALESCE(dv.precio_unitario, v.total_venta),
                   COALESCE(dv.subtotal, v.total_venta)
            FROM ventas v
            LEFT JOIN detalle_ventas dv ON v.id_venta = dv.id_venta
            WHERE v.fecha_venta BETWEEN ? AND ?
            ORDER BY v.fecha_venta ASC, v.hora_venta ASC
            """,
            (fecha_inicio_str, fecha_fin_str),
        )
        ventas_lineas = [tuple(row) for row in cursor.fetchall()]

    suma_lineas = None
    if ventas_lineas:
        suma_lineas = sum(float(v[5]) for v in ventas_lineas)

    gastos_mes = obtener_gastos_periodo(fecha_inicio_str, fecha_fin_str)

    def _gasto_key(gr):
        # (concepto, valor, fecha, hora); fecha típico DD-MM-YYYY
        try:
            d = datetime.strptime((gr[2] or "").strip(), "%d-%m-%Y")
        except ValueError:
            d = datetime.min
        return (d, gr[3] or "")

    gastos_mes = sorted(gastos_mes, key=_gasto_key)

    total_gastos = sum(float(g[1]) for g in gastos_mes)
    ganancia_neta = total_ventas - total_gastos

    return {
        "total_ventas": total_ventas,
        "total_gastos": total_gastos,
        "ganancia_neta": ganancia_neta,
        "ventas_por_dia": ventas_por_dia,
        "ventas_lineas": ventas_lineas,
        "suma_lineas_subtotal": suma_lineas,
        "gastos": gastos_mes,
    }


MESES_ES = (
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
)
_DIA_ES_CORTO = ("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom")


def _normaliza_fecha_gasto_a_iso(fecha_str) -> str | None:
    if not fecha_str or not str(fecha_str).strip():
        return None
    s = str(fecha_str).strip()
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _gastos_por_dia_en_rango_iso(fecha_ini_iso: str, fecha_fin_iso: str) -> dict:
    """Suma de gastos por día (clave YYYY-MM-DD) en el rango."""
    agg = defaultdict(float)
    for row in obtener_gastos_periodo(fecha_ini_iso, fecha_fin_iso):
        valor = float(row[1] or 0)
        fec = row[2]
        iso = _normaliza_fecha_gasto_a_iso(fec)
        if iso and fecha_ini_iso <= iso <= fecha_fin_iso:
            agg[iso] += valor
    return agg


def num_semanas_en_mes(year: int, month: int) -> int:
    _, dim = calendar.monthrange(year, month)
    return (dim + 6) // 7


def rango_semana_del_mes(year: int, month: int, n_semana: int) -> tuple[str, str] | None:
    """
    Semana 1 = días 1–7, semana 2 = 8–14, … del mes calendario.
    Devuelve (fecha_inicio, fecha_fin) en YYYY-MM-DD o None si la semana no existe.
    """
    _, dim = calendar.monthrange(year, month)
    if n_semana < 1:
        return None
    d0 = (n_semana - 1) * 7 + 1
    if d0 > dim:
        return None
    d1 = min(n_semana * 7, dim)
    fi = datetime(year, month, d0).strftime("%Y-%m-%d")
    ff = datetime(year, month, d1).strftime("%Y-%m-%d")
    return fi, ff


def _ventas_total_dia(fecha_iso: str) -> float:
    if not cursor:
        return 0.0
    cursor.execute(
        "SELECT COALESCE(SUM(total_venta), 0) FROM ventas WHERE fecha_venta = ?",
        (fecha_iso,),
    )
    return float(cursor.fetchone()[0] or 0)


def _iter_dias_iso(fecha_ini_iso: str, fecha_fin_iso: str):
    a = datetime.strptime(fecha_ini_iso, "%Y-%m-%d").date()
    b = datetime.strptime(fecha_fin_iso, "%Y-%m-%d").date()
    d = a
    while d <= b:
        yield d.strftime("%Y-%m-%d")
        d += timedelta(days=1)


def _dia_tiene_registros(fecha_iso: str) -> bool:
    """Hay al menos una venta o un gasto guardado ese día."""
    if not cursor:
        return False
    try:
        cursor.execute("SELECT 1 FROM ventas WHERE fecha_venta = ? LIMIT 1", (fecha_iso,))
        if cursor.fetchone():
            return True
        if _gastos_por_dia_en_rango_iso(fecha_iso, fecha_iso).get(fecha_iso, 0) > 0:
            return True
        dd = datetime.strptime(fecha_iso, "%Y-%m-%d").strftime("%d-%m-%Y")
        cursor.execute("SELECT 1 FROM gastos WHERE fecha = ? LIMIT 1", (dd,))
        return bool(cursor.fetchone())
    except (sqlite3.Error, ValueError, TypeError):
        return False


def _anos_con_actividad() -> list[int]:
    """Años en los que existe al menos una venta o un gasto con fecha válida."""
    ys: set[int] = set()
    if not cursor:
        return [datetime.now().year]
    try:
        cursor.execute(
            """
            SELECT DISTINCT cast(substr(fecha_venta, 1, 4) AS integer) AS y
            FROM ventas
            WHERE fecha_venta IS NOT NULL AND length(fecha_venta) >= 4
            """
        )
        for (yy,) in cursor.fetchall():
            if yy is not None and 2000 <= int(yy) <= 2100:
                ys.add(int(yy))
        cursor.execute("SELECT fecha FROM gastos WHERE fecha IS NOT NULL")
        for (fec,) in cursor.fetchall():
            iso = _normaliza_fecha_gasto_a_iso(fec)
            if iso:
                ys.add(int(iso[:4]))
    except (sqlite3.Error, ValueError, TypeError):
        pass
    if not ys:
        return [datetime.now().year]
    return sorted(ys, reverse=True)


def _meses_con_actividad_en_anio(year: int) -> list[int]:
    """Meses (1–12) del año con ventas o gastos registrados."""
    ms: set[int] = set()
    if not cursor:
        return []
    try:
        cursor.execute(
            """
            SELECT DISTINCT cast(strftime('%m', fecha_venta) AS integer) AS m
            FROM ventas
            WHERE fecha_venta BETWEEN ? AND ?
            """,
            (f"{year}-01-01", f"{year}-12-31"),
        )
        for (mm,) in cursor.fetchall():
            if mm is not None and 1 <= int(mm) <= 12:
                ms.add(int(mm))
        cursor.execute("SELECT fecha FROM gastos WHERE fecha IS NOT NULL")
        for (fec,) in cursor.fetchall():
            iso = _normaliza_fecha_gasto_a_iso(fec)
            if iso and int(iso[:4]) == year:
                ms.add(int(iso[5:7]))
    except (sqlite3.Error, ValueError, TypeError):
        pass
    return sorted(ms)


def _semanas_con_actividad_en_mes(year: int, month: int) -> list[int]:
    """Números de semana del mes (bloques 1–7, 8–14, …) donde al menos un día tiene datos."""
    sems: list[int] = []
    for ns in range(1, num_semanas_en_mes(year, month) + 1):
        r = rango_semana_del_mes(year, month, ns)
        if not r:
            continue
        fi, ff = r
        if any(_dia_tiene_registros(d) for d in _iter_dias_iso(fi, ff)):
            sems.append(ns)
    return sems


def _fechas_calendario_mes_dm(year: int, month: int) -> tuple[str, str]:
    """Inicio y fin del mes calendario (dd/mm/yyyy)."""
    _, dim = calendar.monthrange(year, month)
    fi = datetime(year, month, 1).strftime("%d/%m/%Y")
    ff = datetime(year, month, dim).strftime("%d/%m/%Y")
    return fi, ff


def _fechas_datos_mes_avance(year: int, month: int) -> tuple[str, str]:
    """
    Rango ISO para sumar ventas/gastos: mes completo si ya pasó;
    mes en curso: del día 1 hasta hoy (avance). Mes futuro: sin rango útil (fi, fi).
    """
    _, dim = calendar.monthrange(year, month)
    fi = f"{year}-{month:02d}-01"
    ff_cal = f"{year}-{month:02d}-{dim:02d}"
    today = datetime.now().date()
    last = datetime.strptime(ff_cal, "%Y-%m-%d").date()
    cur = (today.year, today.month)
    if (year, month) == cur:
        ff = min(today, last).strftime("%Y-%m-%d")
    elif year < today.year or (year == today.year and month < today.month):
        ff = ff_cal
    else:
        return fi, fi
    return fi, ff


def _ruta_pdf_mes_reciente(year: int, month: int) -> tuple[str | None, str | None]:
    """Último PDF mensual guardado para ese mes (fecha_inicio = primer día). Devuelve (ruta_pdf, id_reporte o None)."""
    fi = f"{year}-{month:02d}-01"
    if not cursor:
        return None, None
    try:
        cursor.execute(
            """
            SELECT id_reporte, ruta_pdf FROM reportes
            WHERE tipo = 'mensual' AND fecha_inicio = ?
            ORDER BY id_reporte DESC LIMIT 1
            """,
            (fi,),
        )
        row = cursor.fetchone()
        if row and row[1] and os.path.exists(row[1]):
            return row[1], str(row[0])
        if row:
            return row[1], str(row[0])
    except (sqlite3.Error, TypeError, ValueError):
        pass
    return None, None


# 📊 Report Functions
def generar_reporte_diario(ventana_principal):
    """Prepares and displays the daily sales report."""
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    abrir_reporte_detallado(ventana_principal, "Reporte Diario", fecha_actual, fecha_actual)

def generar_reporte_semanal(ventana_principal):
    """Ventana de reportes por semana del mes (ganancia por día y totales)."""
    abrir_reportes_semanales(ventana_principal)


def abrir_reporte_detallado(ventana_principal, titulo, fecha_inicio_str, fecha_fin_str):
    """Opens a window with a detailed sales table for a given period with expenses included."""
    if not cursor:
        return
    
    ventana_reporte = tk.Toplevel(ventana_principal)
    ventana_reporte.title(f"{titulo} · VmPOS")
    ventana_reporte.configure(bg=T.BG_APP)
    ventana_reporte.transient(ventana_principal)
    ventana_reporte.grab_set()
    try:
        ventana_reporte.minsize(720, 440)
    except (tk.TclError, Exception):
        pass
    centrar_ventana(ventana_reporte, 1100, 680, ventana_principal)
    _ttk_tree_theme(ventana_reporte)

    root = tk.Frame(ventana_reporte, bg=T.BG_APP)
    root.pack(fill=tk.BOTH, expand=True)

    hdr = tk.Frame(root, bg=T.POS_HEADER, height=72)
    hdr.pack(fill=tk.X)
    hdr.pack_propagate(False)
    hdr_l = tk.Frame(hdr, bg=T.POS_HEADER)
    hdr_l.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=(12, 14))
    tk.Label(hdr_l, text=titulo, font=F_TITLE, bg=T.POS_HEADER, fg=T.WHITE, anchor="w").pack(anchor="w")
    tk.Label(
        hdr_l,
        text=f"{fecha_inicio_str}  ·  {fecha_fin_str}",
        font=F_SMALL,
        bg=T.POS_HEADER,
        fg=T.HEADER_TEXT_DIM,
        anchor="w",
    ).pack(anchor="w", pady=(4, 0))

    main_frame = tk.Frame(root, bg=T.BG_APP)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(12, 14))

    tablas_frame = tk.Frame(main_frame, bg=T.BG_APP)

    def _bloque_tabla(encabezado, color_raya):
        outer = tk.Frame(tablas_frame, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
        bar = tk.Frame(outer, bg=color_raya, height=3)
        bar.pack(fill=tk.X)
        tk.Label(outer, text=encabezado, font=F_BODY_B, bg=T.BG_CARD, fg=T.TEXT).pack(fill=tk.X, padx=10, pady=(8, 4))
        inner_tv = tk.Frame(outer, bg=T.BG_CARD)
        inner_tv.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 10))
        return outer, inner_tv

    ventas_frame, vf_inner = _bloque_tabla("Ventas del período", T.STAT_3)
    gastos_frame, gf_inner = _bloque_tabla("Gastos del período", T.WARN)

    columnas_ventas = ("Fecha", "Hora", "Producto", "Cant.", "P. Unit.", "Subtotal")
    tabla_ventas = ttk.Treeview(vf_inner, columns=columnas_ventas, show="headings", height=12)
    tabla_ventas.pack(fill=tk.BOTH, expand=True)
    widths_ventas = [80, 60, 180, 50, 80, 100]
    for i, col in enumerate(columnas_ventas):
        tabla_ventas.heading(col, text=col)
        tabla_ventas.column(col, width=widths_ventas[i], anchor="center")

    columnas_gastos = ("Fecha", "Hora", "Concepto", "Valor")
    tabla_gastos = ttk.Treeview(gf_inner, columns=columnas_gastos, show="headings", height=12)
    tabla_gastos.pack(fill=tk.BOTH, expand=True)
    widths_gastos = [80, 60, 200, 100]
    for i, col in enumerate(columnas_gastos):
        tabla_gastos.heading(col, text=col)
        tabla_gastos.column(col, width=widths_gastos[i], anchor="center")

    bind_reflow_pack(
        tablas_frame,
        [
            (
                ventas_frame,
                {"side": tk.LEFT, "fill": tk.BOTH, "expand": True, "padx": (0, 8)},
                {"fill": tk.BOTH, "expand": True, "pady": (0, 10)},
            ),
            (
                gastos_frame,
                {"side": tk.LEFT, "fill": tk.BOTH, "expand": True, "padx": (8, 0)},
                {"fill": tk.BOTH, "expand": True, "pady": (0, 10)},
            ),
        ],
        umbral=900,
        debounce_ms=80,
    )
    tablas_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    # Obtener y mostrar datos de VENTAS
    total_ventas_periodo = 0
    try:
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('ventas', 'detalle_ventas')
        """)
        tablas_existentes = [row[0] for row in cursor.fetchall()]
    
        if "ventas" not in tablas_existentes:
            ventas_periodo = []
        elif "detalle_ventas" not in tablas_existentes:
            cursor.execute("""
                SELECT fecha_venta, hora_venta, 'Venta General' as producto, 1 as cantidad, total_venta, total_venta
                FROM ventas
                WHERE fecha_venta BETWEEN ? AND ?
                ORDER BY fecha_venta DESC, hora_venta DESC
            """, (fecha_inicio_str, fecha_fin_str))
            ventas_periodo = cursor.fetchall()
        else:
            cursor.execute("""
                SELECT v.fecha_venta, v.hora_venta, 
                   COALESCE(dv.nombre_producto, 'Venta General') as nombre_producto, 
                   COALESCE(dv.cantidad, 1) as cantidad, 
                   COALESCE(dv.precio_unitario, v.total_venta) as precio_unitario, 
                   COALESCE(dv.subtotal, v.total_venta) as subtotal
                FROM ventas v
                LEFT JOIN detalle_ventas dv ON v.id_venta = dv.id_venta
                WHERE v.fecha_venta BETWEEN ? AND ?
                ORDER BY v.fecha_venta DESC, v.hora_venta DESC
            """, (fecha_inicio_str, fecha_fin_str))
            ventas_periodo = cursor.fetchall()
        
        for venta in ventas_periodo:
            tabla_ventas.insert(
                "",
                tk.END,
                values=(
                    venta[0],
                    venta[1],
                    venta[2],
                    venta[3],
                    formato_peso(venta[4]),
                    formato_peso(venta[5]),
                ),
            )
            total_ventas_periodo += venta[5]

    except Exception as e:
        messagebox.showerror("Error al cargar ventas", str(e), parent=ventana_reporte)

    total_gastos_periodo = 0
    gastos_periodo = obtener_gastos_periodo(fecha_inicio_str, fecha_fin_str)
    for gasto in gastos_periodo:
        tabla_gastos.insert(
            "",
            tk.END,
            values=(gasto[2], gasto[3], gasto[0], formato_peso(gasto[1])),
        )
        total_gastos_periodo += gasto[1]

    ganancia_neta = total_ventas_periodo - total_gastos_periodo

    resumen_frame = tk.Frame(main_frame, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
    resumen_frame.pack(fill=tk.X, pady=(4, 0))
    rz = tk.Frame(resumen_frame, bg=T.BG_CARD)
    rz.pack(fill=tk.X, padx=14, pady=(12, 8))
    tk.Label(rz, text="Resumen del período", font=F_BODY_B, bg=T.BG_CARD, fg=T.TEXT).pack(anchor="w")

    resumen_grid = tk.Frame(resumen_frame, bg=T.BG_SUBTLE, highlightbackground=T.BORDER, highlightthickness=1)
    resumen_grid.pack(fill=tk.X, padx=12, pady=(0, 12))

    resumen_rows = (
        ("Total ventas:", formato_peso(total_ventas_periodo), T.STAT_3),
        ("Total gastos:", formato_peso(total_gastos_periodo), T.WARN),
        ("Ganancia neta:", formato_peso(ganancia_neta), T.STAT_1 if ganancia_neta >= 0 else T.DANGER),
    )
    for label, valor, clr in resumen_rows:
        rowf = tk.Frame(resumen_grid, bg=T.BG_SUBTLE)
        rowf.pack(fill=tk.X, padx=12, pady=6)
        tk.Label(rowf, text=label, font=F_BODY_B, bg=T.BG_SUBTLE, fg=T.TEXT_MUTED).pack(side=tk.LEFT)
        tk.Label(rowf, text=valor, font=F_STAT, bg=T.BG_SUBTLE, fg=clr).pack(side=tk.RIGHT)


def abrir_reportes_semanales(ventana_principal):
    """
    Reporte por «semana del mes» (bloques 1–7, 8–14, …): lista diaria de ventas,
    gastos y ganancia. Año, mes y semana se limitan a periodos con datos guardados
    (ventas o gastos) en la base.
    """
    if not cursor:
        return

    w = tk.Toplevel(ventana_principal)
    w.title("Reportes semanales · VmPOS")
    w.configure(bg=T.BG_APP)
    w.transient(ventana_principal)
    w.grab_set()
    try:
        w.minsize(720, 500)
    except (tk.TclError, Exception):
        pass
    centrar_ventana(w, 960, 600, ventana_principal)
    _ttk_tree_theme(w)

    root = tk.Frame(w, bg=T.BG_APP)
    root.pack(fill=tk.BOTH, expand=True)

    hdr = tk.Frame(root, bg=T.POS_HEADER, height=76)
    hdr.pack(fill=tk.X)
    hdr.pack_propagate(False)
    hl = tk.Frame(hdr, bg=T.POS_HEADER)
    hl.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=(12, 14))
    tk.Label(hl, text="Reportes semanales", font=F_TITLE, bg=T.POS_HEADER, fg=T.WHITE).pack(anchor="w")
    tk.Label(
        hl,
        text="Solo aparecen año, mes y semanas en los que ya hay ventas o gastos guardados.",
        font=F_SMALL,
        bg=T.POS_HEADER,
        fg=T.HEADER_TEXT_DIM,
    ).pack(anchor="w", pady=(4, 0))

    outer = tk.Frame(root, bg=T.BG_APP)
    outer.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

    filt = tk.Frame(outer, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
    filt.pack(fill=tk.X, pady=(0, 10))
    ff = tk.Frame(filt, bg=T.BG_CARD)
    ff.pack(fill=tk.X, padx=12, pady=10)

    _filt = {"mes": [], "sem": []}

    tk.Label(ff, text="Año", font=F_BODY_B, bg=T.BG_CARD, fg=T.TEXT).grid(row=0, column=0, sticky="w", padx=(0, 8))
    anios_datos = _anos_con_actividad()
    cb_anio = ttk.Combobox(ff, values=tuple(str(y) for y in anios_datos), state="readonly", width=7)
    cb_anio.set(str(anios_datos[0]))
    cb_anio.grid(row=0, column=1, sticky="w", padx=(0, 20))

    tk.Label(ff, text="Mes", font=F_BODY_B, bg=T.BG_CARD, fg=T.TEXT).grid(row=0, column=2, sticky="w", padx=(0, 8))
    cb_mes = ttk.Combobox(ff, state="readonly", width=14)
    cb_mes.grid(row=0, column=3, sticky="w", padx=(0, 20))

    tk.Label(ff, text="Semana", font=F_BODY_B, bg=T.BG_CARD, fg=T.TEXT).grid(row=0, column=4, sticky="w", padx=(0, 8))
    cb_sem = ttk.Combobox(ff, state="readonly", width=4)
    cb_sem.grid(row=0, column=5, sticky="w", padx=(0, 16))

    lbl_rango = tk.Label(ff, text="", font=F_SMALL, bg=T.BG_CARD, fg=T.TEXT_MUTED)
    lbl_rango.grid(row=1, column=0, columnspan=6, sticky="w", pady=(10, 0))

    card = tk.Frame(outer, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
    card.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
    bar = tk.Frame(card, bg=T.STAT_1, height=3)
    bar.pack(fill=tk.X)
    tw_wrap = tk.Frame(card, bg=T.BG_CARD)
    tw_wrap.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    cols = ("dia", "fecha", "ventas", "gastos", "ganancia")
    tree = ttk.Treeview(tw_wrap, columns=cols, show="headings", height=12)
    tree.heading("dia", text="Día")
    tree.heading("fecha", text="Fecha")
    tree.heading("ventas", text="Ventas del día")
    tree.heading("gastos", text="Gastos del día")
    tree.heading("ganancia", text="Ganancia del día")
    tree.column("dia", width=52, anchor="center", stretch=False)
    tree.column("fecha", width=120, anchor="center")
    tree.column("ventas", width=130, anchor="e")
    tree.column("gastos", width=130, anchor="e")
    tree.column("ganancia", width=130, anchor="e")
    tree.pack(fill=tk.BOTH, expand=True)

    sumf = tk.Frame(outer, bg=T.BG_SUBTLE, highlightbackground=T.BORDER, highlightthickness=1)
    sumf.pack(fill=tk.X, pady=(0, 10))
    var_tv = tk.StringVar(value="—")
    var_tg = tk.StringVar(value="—")
    var_gan = tk.StringVar(value="—")
    sf = tk.Frame(sumf, bg=T.BG_SUBTLE)
    sf.pack(fill=tk.X, padx=12, pady=10)
    tk.Label(sf, text="Total ventas (semana):", font=F_BODY_B, bg=T.BG_SUBTLE, fg=T.TEXT_MUTED).grid(
        row=0, column=0, sticky="w"
    )
    tk.Label(sf, textvariable=var_tv, font=F_STAT, bg=T.BG_SUBTLE, fg=T.STAT_3).grid(row=0, column=1, sticky="e", padx=(24, 0))
    tk.Label(sf, text="Total gastos:", font=F_BODY_B, bg=T.BG_SUBTLE, fg=T.TEXT_MUTED).grid(row=1, column=0, sticky="w", pady=(6, 0))
    tk.Label(sf, textvariable=var_tg, font=F_STAT, bg=T.BG_SUBTLE, fg=T.WARN).grid(row=1, column=1, sticky="e", padx=(24, 0), pady=(6, 0))
    tk.Label(sf, text="Ganancia neta (semana):", font=F_BODY_B, bg=T.BG_SUBTLE, fg=T.TEXT_MUTED).grid(
        row=2, column=0, sticky="w", pady=(6, 0)
    )
    tk.Label(sf, textvariable=var_gan, font=F_STAT, bg=T.BG_SUBTLE, fg=T.STAT_1).grid(
        row=2, column=1, sticky="e", padx=(24, 0), pady=(6, 0)
    )
    sf.grid_columnconfigure(1, weight=1)

    btnf = tk.Frame(outer, bg=T.BG_APP)
    btnf.pack(fill=tk.X)

    def _refrescar_meses(_e=None):
        try:
            y = int(cb_anio.get())
        except (ValueError, TypeError, tk.TclError):
            _filt["mes"] = []
            cb_mes.set("")
            cb_mes["values"] = ()
        return
        _filt["mes"] = _meses_con_actividad_en_anio(y)
        if not _filt["mes"]:
            cb_mes.set("")
            cb_mes["values"] = ()
            return
        cb_mes["values"] = tuple(MESES_ES[m - 1] for m in _filt["mes"])
        cb_mes.current(0)

    def _refrescar_semanas(_e=None):
        if not _filt["mes"]:
            _filt["sem"] = []
            cb_sem.set("")
            cb_sem["values"] = ()
            return
        try:
            y = int(cb_anio.get())
            mi = cb_mes.current()
            if mi < 0 or mi >= len(_filt["mes"]):
                return
            m = _filt["mes"][mi]
        except (ValueError, TypeError, tk.TclError):
            return
        _filt["sem"] = _semanas_con_actividad_en_mes(y, m)
        if not _filt["sem"]:
            cb_sem.set("")
            cb_sem["values"] = ()
            return
        cb_sem["values"] = tuple(str(s) for s in _filt["sem"])
        cb_sem.current(0)

    def _actualizar_rango_label():
        if not _filt["mes"] or not _filt["sem"]:
            lbl_rango.config(text="")
            return
        try:
            y = int(cb_anio.get())
            mi = cb_mes.current()
            si = cb_sem.current()
            if mi < 0 or si < 0 or mi >= len(_filt["mes"]) or si >= len(_filt["sem"]):
                lbl_rango.config(text="")
                return
            m = _filt["mes"][mi]
            ns = _filt["sem"][si]
        except (ValueError, TypeError, tk.TclError):
            lbl_rango.config(text="")
            return
        r = rango_semana_del_mes(y, m, ns)
        if r:
            fi, ff = r
            lbl_rango.config(
                text=f"Rango: {fi} → {ff} · Semana {ns} del mes ({MESES_ES[m - 1]} {y}). "
                f"Semana 1 = días 1–7, 2 = 8–14, …"
            )
        else:
            lbl_rango.config(text="")

    def _vaciar_resumen_tabla(msg: str):
        tree.delete(*tree.get_children())
        var_tv.set("—")
        var_tg.set("—")
        var_gan.set("—")
        lbl_rango.config(text=msg)

    def cargar_tabla(_e=None):
        """Rellena tabla y totales según año / mes / semana ya elegidos (no altera los combos)."""
        if not _filt["mes"] or not _filt["sem"]:
            _vaciar_resumen_tabla(
                "No hay ventas ni gastos registrados en la base para el año elegido, o no hay semanas con datos en ese mes."
            )
            return
        try:
            y = int(cb_anio.get())
            mi = cb_mes.current()
            si = cb_sem.current()
            if mi < 0 or si < 0 or mi >= len(_filt["mes"]) or si >= len(_filt["sem"]):
                return
            m = _filt["mes"][mi]
            ns = _filt["sem"][si]
        except (ValueError, TypeError, tk.TclError):
            return
        r = rango_semana_del_mes(y, m, ns)
        if not r:
            _vaciar_resumen_tabla("No se pudo calcular el rango de la semana.")
            return
        fi, ff = r
        _actualizar_rango_label()
        gastos_por_dia = _gastos_por_dia_en_rango_iso(fi, ff)
        tree.delete(*tree.get_children())
        tv = tg = 0.0
        for dia_iso in _iter_dias_iso(fi, ff):
            v = _ventas_total_dia(dia_iso)
            g = float(gastos_por_dia.get(dia_iso, 0.0))
            gan = v - g
            tv += v
            tg += g
            wd = datetime.strptime(dia_iso, "%Y-%m-%d").date().weekday()
            dia_txt = _DIA_ES_CORTO[wd]
            fecha_txt = datetime.strptime(dia_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
            tree.insert(
                "",
                tk.END,
                values=(dia_txt, fecha_txt, formato_peso(v), formato_peso(g), formato_peso(gan)),
            )
        gan_s = tv - tg
        var_tv.set(formato_peso(tv))
        var_tg.set(formato_peso(tg))
        var_gan.set(formato_peso(gan_s))

    def ver_detalle_lineas():
        if not _filt["mes"] or not _filt["sem"]:
            messagebox.showwarning("Datos", "No hay semana seleccionable con información guardada.", parent=w)
            return
        try:
            y = int(cb_anio.get())
            mi = cb_mes.current()
            si = cb_sem.current()
            m = _filt["mes"][mi]
            ns = _filt["sem"][si]
        except (ValueError, TypeError, IndexError, tk.TclError):
            return
        r = rango_semana_del_mes(y, m, ns)
        if not r:
            messagebox.showwarning("Semana", "Seleccione una semana válida.", parent=w)
            return
        fi, ff = r
        titulo = f"Semana {ns} · {MESES_ES[m - 1]} {y}"
        abrir_reporte_detallado(ventana_principal, titulo, fi, ff)

    def _on_anio(_e=None):
        _refrescar_meses()
        _refrescar_semanas()
        cargar_tabla()

    def _on_mes(_e=None):
        _refrescar_semanas()
        cargar_tabla()

    tk.Button(
        btnf,
        text="Actualizar vista",
        command=cargar_tabla,
        bg=T.POS_BTN_ALT,
        fg=T.WHITE,
        font=F_BODY_B,
        relief=tk.FLAT,
        padx=14,
        pady=8,
        cursor="hand2",
    ).pack(side=tk.LEFT, padx=(0, 8))
    tk.Button(
        btnf,
        text="Ver detalle de líneas (ventas / gastos)",
        command=ver_detalle_lineas,
        bg=T.STAT_2,
        fg=T.WHITE,
        font=F_BODY_B,
        relief=tk.FLAT,
        padx=14,
        pady=8,
        cursor="hand2",
    ).pack(side=tk.LEFT)

    cb_anio.bind("<<ComboboxSelected>>", _on_anio)
    cb_mes.bind("<<ComboboxSelected>>", _on_mes)
    cb_sem.bind("<<ComboboxSelected>>", cargar_tabla)

    _on_anio()


def _estilo_pdf_tabla(hdr_hex, grid_hex, fila_hex):
    """Estilo repetible para tablas PDF (cabecera + cuerpo + rejilla)."""
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(hdr_hex)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("TOPPADDING", (0, 1), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 3),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor(fila_hex)),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor(grid_hex)),
        ]
    )


def generar_reporte_mensual_pdf(anio=None, mes=None, parent=None):
    """
    PDF mensual: ventas por día, líneas, gastos y cierre.
    ``anio``/``mes`` opcionales (por defecto mes en curso). El rango de datos sigue
    el avance del mes (hasta hoy si es el mes actual).
    """
    if not REPORTLAB_DISPONIBLE:
        messagebox.showerror(
            "Error",
            "ReportLab no está disponible. No se pueden generar reportes PDF.",
            parent=parent,
        )
        return

    if not cursor:
        return
    try:
        os.makedirs(pdf_dir, exist_ok=True)
        ahora = datetime.now()
        y = int(anio) if anio is not None else ahora.year
        m = int(mes) if mes is not None else ahora.month
        fecha_inicio_str, fecha_fin_str = _fechas_datos_mes_avance(y, m)

        d = _recolectar_reporte_financiero_mes(fecha_inicio_str, fecha_fin_str)
        total_ventas = d["total_ventas"]
        total_gastos = d["total_gastos"]
        ganancia_neta = d["ganancia_neta"]
        ventas_por_dia = d["ventas_por_dia"]
        ventas_lineas = d["ventas_lineas"]
        gastos_mes = d["gastos"]
        suma_lineas = d["suma_lineas_subtotal"]

        pdf_path = os.path.join(pdf_dir, f"Reporte_Mensual_Completo_{y}-{m:02d}.pdf")
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=landscape(letter),
            leftMargin=42,
            rightMargin=42,
            topMargin=42,
            bottomMargin=42,
        )
        story = []
        
        styles = getSampleStyleSheet()
        # No volver a registrar "Heading1"/"Normal": ya existen y ``add`` duplicado lanza error.
        styles["Heading1"].fontSize = 18
        styles["Heading1"].fontName = "Helvetica-Bold"
        styles["Normal"].fontSize = 10

        story.append(Paragraph("Reporte financiero mensual", styles["Heading1"]))
        sufijo_avance = " (acumulado hasta la fecha indicada)" if (y, m) == (ahora.year, ahora.month) else ""
        story.append(
            Paragraph(f"Periodo analizado{sufijo_avance}: {fecha_inicio_str} · {fecha_fin_str}", styles["Normal"])
        )
        story.append(Spacer(1, 0.14 * inch))

        # — Resumen ejecutivo (totales globales desde tabla ventas y gastos)
        story.append(Paragraph("<b>Resumen ejecutivo</b>", styles["Normal"]))
        story.append(Spacer(1, 0.06 * inch))
        tabla_resumen = Table(
            [
                ["Concepto", "Valor"],
                ["Total ventas del mes", formato_peso(total_ventas)],
                ["Total gastos del mes", formato_peso(total_gastos)],
                ["Resultado neto (ventas − gastos)", formato_peso(ganancia_neta)],
            ],
            colWidths=[3.9 * inch, 2.2 * inch],
        )
        est_res = TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#cbd5e1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke] * 3),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ]
        )
        tabla_resumen.setStyle(est_res)
        story.append(tabla_resumen)
        story.append(Spacer(1, 0.18 * inch))

        # — Ventas por día del mes (sumatorio por fecha)
        story.append(Paragraph("<b>Ventas por día</b> (total facturado por fecha)", styles["Normal"]))
        datos_día = [["Fecha", "Total del día (COP)"]]
        for fecha, dia_total in ventas_por_dia:
            datos_día.append([str(fecha), formato_peso(dia_total)])
        datos_día.append(["TOTAL MES", formato_peso(total_ventas)])
        t_día = Table(datos_día, colWidths=[2.8 * inch, 2.4 * inch])
        st_día = _estilo_pdf_tabla("#047857", "#059669", "#ecfdf5")
        st_día.add(("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#d1fae5")))
        st_día.add(("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"))
        t_día.setStyle(st_día)
        story.append(t_día)
        story.append(Spacer(1, 0.16 * inch))

        # — Detalle de líneas (todos los productos / líneas del mes)
        story.append(
            Paragraph("<b>Todas las ventas del mes</b> — líneas de detalle por producto y hora.", styles["Normal"])
        )
        if ventas_lineas:
            data_ln = [["Fecha", "Hora", "Producto", "Cant.", "P. unit.", "Subtotal"]]
            for row in ventas_lineas:
                data_ln.append(
                    [
                        str(row[0]),
                        str(row[1]),
                        str(row[2])[:60],
                        str(row[3]),
                        formato_peso(row[4]),
                        formato_peso(row[5]),
                    ]
                )
            if suma_lineas is not None:
                data_ln.append(
                    ["", "", "", "", "Subtotal (suma de líneas)", formato_peso(suma_lineas)]
                )
            t_ln = Table(
                data_ln,
                colWidths=[0.95 * inch, 0.75 * inch, 3.15 * inch, 0.55 * inch, 1.0 * inch, 1.15 * inch],
            )
            st_ln = _estilo_pdf_tabla("#166534", "#22c55e", "#f0fdf4")
            last_r = len(data_ln) - 1
            st_ln.add(("BACKGROUND", (0, last_r), (-1, last_r), colors.HexColor("#dcfce7")))
            st_ln.add(("FONTNAME", (4, last_r), (5, last_r), "Helvetica-Bold"))
            st_ln.add(("ALIGN", (4, last_r), (5, last_r), "RIGHT"))
            t_ln.setStyle(st_ln)
            story.append(t_ln)
        else:
            story.append(Paragraph("<i>No hay ventas registradas en el mes para el detalle por líneas.</i>", styles["Normal"]))
        story.append(Spacer(1, 0.16 * inch))

        # — Gastos
        story.append(Paragraph("<b>Gastos del mes</b> (fecha y hora de registro)", styles["Normal"]))
        if gastos_mes:
            data_g = [["Fecha", "Hora", "Concepto", "Valor"]]
            for gasto in gastos_mes:
                data_g.append([str(gasto[2]), str(gasto[3]), str(gasto[0])[:55], formato_peso(gasto[1])])
            data_g.append(["", "", "TOTAL GASTOS", formato_peso(total_gastos)])
            tg = Table(data_g, colWidths=[1.1 * inch, 0.95 * inch, 4.1 * inch, 1.4 * inch])
            stg = _estilo_pdf_tabla("#c2410c", "#ea580c", "#fff7ed")
            stg.add(("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"))
            stg.add(("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#ffedd5")))
            stg.add(("SPAN", (0, -1), (1, -1)))
            stg.add(("ALIGN", (2, -1), (2, -1), "RIGHT"))
            tg.setStyle(stg)
            story.append(tg)
        else:
            story.append(Paragraph("<i>No hay gastos registrados en este periodo.</i>", styles["Normal"]))
        story.append(Spacer(1, 0.16 * inch))

        # — Cierre explícito
        story.append(Paragraph("<b>Cierre del mes</b>", styles["Normal"]))
        cierre = Table(
            [
                ["Indicador", "Monto"],
                ["Total ventas (tabla ventas)", formato_peso(total_ventas)],
                ["Total gastos", formato_peso(total_gastos)],
                ["Ganancia neta = ventas − gastos", formato_peso(ganancia_neta)],
            ],
            colWidths=[4.2 * inch, 2.2 * inch],
        )
        cierre.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#64748b")),
                    ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.HexColor("#f8fafc"), colors.HexColor("#f1f5f9")]),
                    ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e0f2fe")),
                ]
            )
        )
        story.append(cierre)

        doc.build(story)

        resumen = (
            f"Ventas: {formato_peso(total_ventas)} | Gastos: {formato_peso(total_gastos)} | "
            f"Ganancia: {formato_peso(ganancia_neta)}"
        )
        cursor.execute(
            """
            INSERT INTO reportes (tipo, fecha_inicio, fecha_fin, resumen, ruta_pdf)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("mensual", fecha_inicio_str, fecha_fin_str, resumen, pdf_path),
        )
        conn.commit()

        messagebox.showinfo(
            "Reporte mensual",
            f"Reporte PDF generado correctamente.\n\n{resumen}\n\n{pdf_path}",
            parent=parent,
        )
        
    except Exception as e:
        messagebox.showerror("Error al generar reporte", f"Error: {str(e)}", parent=parent)
        conn.rollback()

def generar_excel_mensual(anio=None, mes=None, parent=None):
    """
    Excel del mes: resumen, ventas por día, líneas, gastos e histórico.
    ``anio``/``mes`` opcionales; el periodo numérico sigue el avance del mes (hasta hoy si aplica).
    """
    if not OPENPYXL_DISPONIBLE:
        messagebox.showerror(
            "Error",
            "OpenPyXL no está disponible. No se pueden generar reportes Excel.",
            parent=parent,
        )
        return
        
    if not cursor:
        return

    try:
        os.makedirs(excel_dir, exist_ok=True)
        ahora = datetime.now()
        y = int(anio) if anio is not None else ahora.year
        m = int(mes) if mes is not None else ahora.month
        fecha_inicio_str, fecha_fin_str = _fechas_datos_mes_avance(y, m)

        d = _recolectar_reporte_financiero_mes(fecha_inicio_str, fecha_fin_str)
        total_ventas = d["total_ventas"]
        total_gastos = d["total_gastos"]
        ganancia_neta = d["ganancia_neta"]
        ventas_por_dia = d["ventas_por_dia"]
        ventas_lineas = d["ventas_lineas"]
        suma_lineas = d["suma_lineas_subtotal"]
        gastos_mes = d["gastos"]

        excel_path = os.path.join(excel_dir, f"Reporte_Mensual_{y}-{m:02d}.xlsx")
        wb = Workbook()
        wb.remove(wb.active)
        
        header_font = Font(size=16, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="2E7D32", end_color="2E7D32", fill_type="solid")
        subheader_font = Font(size=12, bold=True)
        hoy = datetime.now()

        # — Hoja resumen
        ws_resumen = wb.create_sheet("Resumen Ejecutivo")
        ws_resumen.merge_cells("A1:E1")
        ws_resumen["A1"] = f"REPORTE FINANCIERO MENSUAL — {MESES_ES[m - 1].upper()} {y}"
        ws_resumen["A1"].font = header_font
        ws_resumen["A1"].fill = header_fill
        ws_resumen["A1"].alignment = Alignment(horizontal="center")

        ws_resumen["A3"] = "CONCEPTO"
        ws_resumen["B3"] = "VALOR"
        ws_resumen["A3"].font = subheader_font
        ws_resumen["B3"].font = subheader_font
        
        resumen_data = [
            ("Total ventas (tabla ventas)", total_ventas),
            ("Total gastos", total_gastos),
            ("Resultado neto (ventas − gastos)", ganancia_neta),
        ]
        for i, (concepto, valor) in enumerate(resumen_data, 4):
            ws_resumen[f"A{i}"] = concepto
            ws_resumen[f"B{i}"] = valor
            ws_resumen[f"B{i}"].number_format = "$#,##0"

        r_note = 8
        if suma_lineas is not None and ventas_lineas and abs(suma_lineas - total_ventas) > 0.009:
            ws_resumen.merge_cells(f"A{r_note}:E{r_note}")
            ws_resumen[f"A{r_note}"] = (
                f"Nota: la suma de subtotales ({formato_peso(suma_lineas)}) puede diferir del "
                f"total en ventas ({formato_peso(total_ventas)}) si algún ticket no tiene detalle por producto."
            )

        # — Ventas por día
        ws_dia = wb.create_sheet("Ventas por día")
        h_dia = ["Fecha", "Total del día"]
        for col, h in enumerate(h_dia, 1):
            c = ws_dia.cell(row=1, column=col, value=h)
            c.font = Font(color="FFFFFF", bold=True)
            c.fill = PatternFill(start_color="047857", end_color="047857", fill_type="solid")

        r = 2
        for fecha_d, total_d in ventas_por_dia:
            ws_dia.cell(row=r, column=1, value=fecha_d)
            ws_dia.cell(row=r, column=2, value=total_d).number_format = "$#,##0"
            r += 1
        ws_dia.cell(row=r, column=1, value="TOTAL MES").font = Font(bold=True)
        ws_dia.cell(row=r, column=2, value=total_ventas).number_format = "$#,##0"
        ws_dia.cell(row=r, column=2).font = Font(bold=True)

        # — Detalle de líneas de venta
        ws_ventas = wb.create_sheet("Detalle líneas ventas")
        headers_ventas = ["Fecha", "Hora", "Producto", "Cantidad", "Precio Unitario", "Subtotal"]
        for col, header in enumerate(headers_ventas, 1):
            cell = ws_ventas.cell(row=1, column=col, value=header)
            cell.font = Font(color="FFFFFF", bold=True)
            cell.fill = PatternFill(start_color="4CAF50", end_color="4CAF50", fill_type="solid")

        rr = 2
        for vn in ventas_lineas:
            ws_ventas.cell(row=rr, column=1, value=vn[0])
            ws_ventas.cell(row=rr, column=2, value=vn[1])
            ws_ventas.cell(row=rr, column=3, value=vn[2])
            ws_ventas.cell(row=rr, column=4, value=vn[3])
            ws_ventas.cell(row=rr, column=5, value=vn[4]).number_format = "$#,##0"
            ws_ventas.cell(row=rr, column=6, value=vn[5]).number_format = "$#,##0"
            rr += 1
        if ventas_lineas and suma_lineas is not None:
            ws_ventas.cell(row=rr, column=5, value="Subtotal (suma líneas)").font = Font(bold=True)
            ws_ventas.cell(row=rr, column=6, value=suma_lineas).number_format = "$#,##0"
            ws_ventas.cell(row=rr, column=6).font = Font(bold=True)

        # — Gastos
        ws_gastos = wb.create_sheet("Detalle Gastos")
        headers_gastos = ["Fecha", "Hora", "Concepto", "Valor"]
        for col, header in enumerate(headers_gastos, 1):
            cell = ws_gastos.cell(row=1, column=col, value=header)
            cell.font = Font(color="FFFFFF", bold=True)
            cell.fill = PatternFill(start_color="FF5722", end_color="FF5722", fill_type="solid")

        rg = 2
        for gasto in gastos_mes:
            ws_gastos.cell(row=rg, column=1, value=gasto[2])
            ws_gastos.cell(row=rg, column=2, value=gasto[3])
            ws_gastos.cell(row=rg, column=3, value=gasto[0])
            ws_gastos.cell(row=rg, column=4, value=gasto[1]).number_format = "$#,##0"
            rg += 1
        ws_gastos.cell(row=rg, column=1, value="TOTAL GASTOS").font = Font(bold=True)
        ws_gastos.cell(row=rg, column=2, value="")
        ws_gastos.cell(row=rg, column=3, value="")
        ws_gastos.cell(row=rg, column=4, value=total_gastos).number_format = "$#,##0"
        ws_gastos.cell(row=rg, column=4).font = Font(bold=True)

        # — Histórico (igual que antes)
        ws_historico = wb.create_sheet("Análisis Histórico")
        
        headers_historico = ["Mes/Año", "Total Ventas", "Total Gastos", "Ganancia Neta"]
        for col, header in enumerate(headers_historico, 1):
            cell = ws_historico.cell(row=1, column=col, value=header)
            cell.font = subheader_font
            cell.fill = PatternFill(start_color="2196F3", end_color="2196F3", fill_type="solid")
            cell.font = Font(color="FFFFFF", bold=True)
        
        fecha_hace_12_meses = hoy - timedelta(days=365)
        
        cursor.execute(
            """
            SELECT strftime('%Y-%m', fecha_venta) as mes, SUM(total_venta) as total_ventas
            FROM ventas
            WHERE fecha_venta >= ?
            GROUP BY strftime('%Y-%m', fecha_venta)
            ORDER BY mes DESC
            """,
            (fecha_hace_12_meses.strftime("%Y-%m-%d"),),
        )
        
        ventas_historicas = cursor.fetchall()
        
        row = 2
        for mes_venta in ventas_historicas:
            mes_año = mes_venta[0]
            tv = mes_venta[1]
            
            cursor.execute(
                """
                SELECT SUM(valor) FROM gastos
                WHERE substr(fecha, 7, 4) || '-' || 
                      case when length(substr(fecha, 4, 2)) = 1 then '0' || substr(fecha, 4, 2) else substr(fecha, 4, 2) end
                      = ?
                """,
                (mes_año,),
            )
            
            result = cursor.fetchone()
            gastos_mes_valor = result[0] if result and result[0] else 0
            
            ganancia_mes = tv - gastos_mes_valor
            
            fecha_mes = datetime.strptime(mes_año + "-01", "%Y-%m-%d")
            mes_legible = fecha_mes.strftime("%B %Y")
            
            ws_historico.cell(row=row, column=1, value=mes_legible)
            ws_historico.cell(row=row, column=2, value=tv).number_format = "$#,##0"
            ws_historico.cell(row=row, column=3, value=gastos_mes_valor).number_format = "$#,##0"
            ws_historico.cell(row=row, column=4, value=ganancia_mes).number_format = "$#,##0"
            
            row += 1
        
        for ws in [ws_resumen, ws_dia, ws_ventas, ws_gastos, ws_historico]:
            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except Exception:
                        pass
                ws.column_dimensions[column_letter].width = min(max_length + 2, 55)
        
        wb.save(excel_path)
        
        messagebox.showinfo(
            "Excel generado",
            f"Archivo Excel generado correctamente:\n{excel_path}",
            parent=parent,
        )

        os.startfile(excel_path)
        
    except Exception as e:
        messagebox.showerror("Error", f"Error al generar Excel: {str(e)}", parent=parent)

def abrir_reportes_mensuales(ventana_principal):
    """
    Vista mensual: Inicio/Fin del mes calendario; resumen con datos según avance del mes
    (hasta hoy en el mes en curso). Filtro por año y mes (solo periodos con ventas o gastos).
    """
    if not cursor:
        return
    
    ventana_mensual = tk.Toplevel(ventana_principal)
    ventana_mensual.title("Reportes mensuales · VmPOS")
    ventana_mensual.configure(bg=T.BG_APP)
    ventana_mensual.transient(ventana_principal)
    ventana_mensual.grab_set()
    try:
        ventana_mensual.minsize(720, 480)
    except (tk.TclError, Exception):
        pass
    centrar_ventana(ventana_mensual, 960, 580, ventana_principal)
    _ttk_tree_theme(ventana_mensual)

    root = tk.Frame(ventana_mensual, bg=T.BG_APP)
    root.pack(fill=tk.BOTH, expand=True)

    hdr = tk.Frame(root, bg=T.POS_HEADER, height=76)
    hdr.pack(fill=tk.X)
    hdr.pack_propagate(False)
    hl = tk.Frame(hdr, bg=T.POS_HEADER)
    hl.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=(12, 14))
    tk.Label(hl, text="Reportes mensuales", font=F_TITLE, bg=T.POS_HEADER, fg=T.WHITE).pack(anchor="w")
    tk.Label(
        hl,
        text="Inicio y fin = mes calendario. El resumen acumula ventas y gastos hasta la fecha de corte "
        "(en el mes en curso, hasta hoy). Doble clic abre el PDF si ya fue generado.",
        font=F_SMALL,
        bg=T.POS_HEADER,
        fg=T.HEADER_TEXT_DIM,
        wraplength=820,
        justify="left",
    ).pack(anchor="w", pady=(4, 0))

    outer = tk.Frame(root, bg=T.BG_APP)
    outer.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

    filt = tk.Frame(outer, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
    filt.pack(fill=tk.X, pady=(0, 10))
    ff = tk.Frame(filt, bg=T.BG_CARD)
    ff.pack(fill=tk.X, padx=12, pady=10)

    _filt = {"mes_list": []}

    tk.Label(ff, text="Año", font=F_BODY_B, bg=T.BG_CARD, fg=T.TEXT).grid(row=0, column=0, sticky="w", padx=(0, 8))
    anios_datos = _anos_con_actividad()
    cb_anio = ttk.Combobox(ff, values=tuple(str(y) for y in anios_datos), state="readonly", width=7)
    cb_anio.set(str(anios_datos[0]))
    cb_anio.grid(row=0, column=1, sticky="w", padx=(0, 24))

    tk.Label(ff, text="Mes", font=F_BODY_B, bg=T.BG_CARD, fg=T.TEXT).grid(row=0, column=2, sticky="w", padx=(0, 8))
    cb_mes = ttk.Combobox(ff, state="readonly", width=22)
    cb_mes.grid(row=0, column=3, sticky="w")

    table_card = tk.Frame(outer, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
    table_card.pack(fill=tk.BOTH, expand=True, pady=(0, 12))
    bar = tk.Frame(table_card, bg=T.STAT_2, height=3)
    bar.pack(fill=tk.X)

    tw_frame = tk.Frame(table_card, bg=T.BG_CARD)
    tw_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    lbl_vacio = tk.Label(
        tw_frame,
        text="",
        font=F_SMALL,
        bg=T.BG_CARD,
        fg=T.TEXT_MUTED,
        wraplength=860,
        justify="left",
    )
    lbl_vacio.pack(fill=tk.X, pady=(0, 4))

    tabla_reportes = ttk.Treeview(
        tw_frame,
        columns=("ID", "Periodo", "Fecha Inicio", "Fecha Fin", "Resumen"),
        show="headings",
        height=14,
    )
    tabla_reportes.pack(fill=tk.BOTH, expand=True)

    tabla_reportes.heading("ID", text="ID")
    tabla_reportes.heading("Periodo", text="Periodo")
    tabla_reportes.heading("Fecha Inicio", text="Inicio")
    tabla_reportes.heading("Fecha Fin", text="Fin")
    tabla_reportes.heading("Resumen", text="Resumen")

    tabla_reportes.column("ID", width=52, anchor="center", stretch=False)
    tabla_reportes.column("Periodo", width=88, anchor="center", stretch=False)
    tabla_reportes.column("Fecha Inicio", width=110, anchor="center")
    tabla_reportes.column("Fecha Fin", width=110, anchor="center")
    tabla_reportes.column("Resumen", width=380, stretch=True)

    def _refrescar_meses_combo(_e=None):
        try:
            y = int(cb_anio.get())
        except (ValueError, TypeError, tk.TclError):
            _filt["mes_list"] = []
            cb_mes.set("")
            cb_mes["values"] = ()
            return
        meses_act = _meses_con_actividad_en_anio(y)
        _filt["mes_list"] = meses_act
        if not meses_act:
            cb_mes.set("")
            cb_mes["values"] = ()
            return
        vals = ["Todos los meses"] + [MESES_ES[mm - 1] for mm in meses_act]
        cb_mes["values"] = vals
        hoy = datetime.now()
        if hoy.year == y and hoy.month in meses_act:
            cb_mes.current(1 + meses_act.index(hoy.month))
        else:
            cb_mes.current(0)

    def _meses_a_mostrar() -> tuple[int, list[int]]:
        try:
            y = int(cb_anio.get())
        except (ValueError, TypeError, tk.TclError):
            return datetime.now().year, []
        meses_act = _filt.get("mes_list") or []
        if not meses_act:
            return y, []
        try:
            idx = cb_mes.current()
        except tk.TclError:
            idx = -1
        if idx == 0:
            return y, list(meses_act)
        if idx > 0 and idx - 1 < len(meses_act):
            return y, [meses_act[idx - 1]]
        return y, []

    def cargar_reportes(_e=None):
        tabla_reportes.delete(*tabla_reportes.get_children())
        y, meses_rows = _meses_a_mostrar()
        if not meses_rows:
            lbl_vacio.config(
                text="No hay ventas ni gastos registrados para el año elegido, o elija otro año en el filtro.",
            )
            return
        lbl_vacio.config(text="")
        hoy = datetime.now()
        n = 0
        for m in meses_rows:
            fi_dm, ff_dm = _fechas_calendario_mes_dm(y, m)
            fi_iso, ff_iso = _fechas_datos_mes_avance(y, m)
            d = _recolectar_reporte_financiero_mes(fi_iso, ff_iso)
            tv, tg, gn = d["total_ventas"], d["total_gastos"], d["ganancia_neta"]
            resumen = (
                f"Ventas: {formato_peso(tv)} | Gastos: {formato_peso(tg)} | Ganancia: {formato_peso(gn)}"
            )
            if (y, m) == (hoy.year, hoy.month):
                resumen += " (acumulado a hoy)"
            ruta_pdf, id_rep = _ruta_pdf_mes_reciente(y, m)
            rid = id_rep if id_rep else "—"
            periodo = f"{y}-{m:02d}"
            tabla_reportes.insert(
                "",
                tk.END,
                iid=periodo,
                values=(rid, periodo, fi_dm, ff_dm, resumen),
                tags=(ruta_pdf or "",),
            )
            n += 1
        if n == 0:
            lbl_vacio.config(text="No hay filas que mostrar para el filtro actual.")

    def descargar_pdf():
        seleccionado = tabla_reportes.focus()
        if not seleccionado:
            messagebox.showwarning(
                "Sin selección",
                "Seleccione una fila (mes) para abrir el PDF generado de ese mes.",
                parent=ventana_mensual,
            )
            return
        tags = tabla_reportes.item(seleccionado, "tags")
        ruta_pdf = tags[0] if tags else ""
        if ruta_pdf and os.path.exists(ruta_pdf):
            os.startfile(ruta_pdf)
        else:
            messagebox.showwarning(
                "Sin PDF",
                "Aún no hay un PDF guardado para ese mes. Use «Generar PDF del mes».",
                parent=ventana_mensual,
            )

    def on_double_click(_event):
        descargar_pdf()

    tabla_reportes.bind("<Double-1>", on_double_click)

    def _y_m_desde_seleccion_o_hoy() -> tuple[int, int]:
        sel = tabla_reportes.focus()
        if sel:
            try:
                yy, mm = map(int, sel.split("-", 1))
                return yy, mm
            except (ValueError, TypeError, AttributeError):
                pass
        ahora = datetime.now()
        return ahora.year, ahora.month

    botones_frame = tk.Frame(outer, bg=T.BG_APP)
    botones_frame.pack(fill=tk.X)

    def _btn(txt, cmd, bg, hover):
        b = tk.Button(
            botones_frame,
            text=txt,
            command=cmd,
            bg=bg,
            fg=T.WHITE,
            font=F_BODY_B,
            relief=tk.FLAT,
            padx=14,
            pady=8,
            cursor="hand2",
            activebackground=hover,
            activeforeground=T.WHITE,
        )

        def ent(_e=None):
            b.configure(bg=hover)

        def lev(_e=None):
            b.configure(bg=bg)

        b.bind("<Enter>", ent)
        b.bind("<Leave>", lev)
        return b

    def generar_pdf_y_recargar():
        yy, mm = _y_m_desde_seleccion_o_hoy()
        generar_reporte_mensual_pdf(yy, mm, parent=ventana_mensual)
        cargar_reportes()

    def exportar_excel_mes():
        yy, mm = _y_m_desde_seleccion_o_hoy()
        generar_excel_mensual(yy, mm, parent=ventana_mensual)

    _btn("Generar PDF del mes", generar_pdf_y_recargar, T.STAT_2, "#7c3aed").pack(side=tk.LEFT, padx=(0, 8))
    _btn("Exportar Excel del mes", exportar_excel_mes, T.STAT_3, "#047857").pack(side=tk.LEFT, padx=(0, 8))
    _btn("Abrir PDF seleccionado", descargar_pdf, T.STAT_1, "#0284c7").pack(side=tk.LEFT, padx=(0, 8))

    cb_anio.bind("<<ComboboxSelected>>", lambda e: (_refrescar_meses_combo(), cargar_reportes()))
    cb_mes.bind("<<ComboboxSelected>>", cargar_reportes)

    _refrescar_meses_combo()
    cargar_reportes()

def generar_grafico_ventas_mensuales(ventana_principal):
    """Genera un gráfico de ventas mensuales históricas."""
    if not MATPLOTLIB_DISPONIBLE:
        messagebox.showerror("❌ Error", "Matplotlib no está disponible. No se pueden generar gráficos.")
        return
        
    try:
        
        # Crear ventana para el gráfico
        ventana_grafico = tk.Toplevel(ventana_principal)
        ventana_grafico.title("Análisis de ventas mensuales · VmPOS")
        ventana_grafico.configure(bg=T.BG_APP)
        centrar_ventana(ventana_grafico, 1020, 640, ventana_principal)

        root_graf = tk.Frame(ventana_grafico, bg=T.BG_APP)
        root_graf.pack(fill=tk.BOTH, expand=True)
        
        # Obtener datos de los últimos 12 meses
        fecha_hace_12_meses = datetime.now() - timedelta(days=365)
        
        cursor.execute("""
            SELECT strftime('%Y-%m', fecha_venta) as mes, 
                   SUM(total_venta) as total_ventas,
                   COUNT(*) as num_ventas
            FROM ventas
            WHERE fecha_venta >= ?
            GROUP BY strftime('%Y-%m', fecha_venta)
            ORDER BY mes ASC
        """, (fecha_hace_12_meses.strftime("%Y-%m-%d"),))
        
        datos = cursor.fetchall()
        
        if not datos:
            messagebox.showinfo("Sin datos", "No hay datos suficientes para generar el gráfico.", parent=ventana_principal)
            ventana_grafico.destroy()
            return
        
        # Procesar datos
        meses = []
        ventas = []
        num_transacciones = []
        
        for mes, total_venta, num_venta in datos:
            fecha_mes = datetime.strptime(mes + "-01", "%Y-%m-%d")
            meses.append(fecha_mes)
            ventas.append(total_venta)
            num_transacciones.append(num_venta)
        
        # Crear gráfico
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        fig.suptitle('Análisis de Ventas Mensuales - Últimos 12 Meses', fontsize=16, fontweight='bold')
        
        # Gráfico 1: Total de ventas
        ax1.plot(meses, ventas, marker='o', linewidth=2, markersize=8, color=T.STAT_3)
        ax1.fill_between(meses, ventas, alpha=0.28, color=T.STAT_3)
        ax1.set_title('Total de Ventas por Mes', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Ventas (COP)', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # Gráfico 2: Número de transacciones
        ax2.bar(meses, num_transacciones, color=T.STAT_4, alpha=0.85)
        ax2.set_title('Número de Transacciones por Mes', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Número de Transacciones', fontsize=12)
        ax2.set_xlabel('Mes', fontsize=12)
        ax2.grid(True, alpha=0.3, axis='y')
        
        # Formatear fechas en el eje X
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        
        # Integrar gráfico en la ventana
        canvas = FigureCanvasTkAgg(fig, root_graf)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=16, pady=(12, 8))
        
        stats_frame = tk.Frame(root_graf, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
        stats_frame.pack(fill=tk.X, padx=16, pady=(0, 14))
        
        # Calcular estadísticas
        promedio_ventas = sum(ventas) / len(ventas)
        mes_mejor = meses[ventas.index(max(ventas))]
        mes_peor = meses[ventas.index(min(ventas))]
        
        tk.Label(
            stats_frame,
            text="Resumen del período",
            font=F_BODY_B,
            bg=T.BG_CARD,
            fg=T.TEXT,
        ).pack(anchor="w", padx=12, pady=(10, 4))

        stats_text = (
            f"Promedio mensual: ${promedio_ventas:,.0f}\n"
            f"Mejor mes: {mes_mejor.strftime('%B %Y')} (${max(ventas):,.0f})\n"
            f"Peor mes: {mes_peor.strftime('%B %Y')} (${min(ventas):,.0f})\n"
            f"Total en el período: ${sum(ventas):,.0f}"
        )

        tk.Label(stats_frame, text=stats_text, font=F_BODY, bg=T.BG_CARD, fg=T.TEXT_MUTED, justify="left").pack(
            anchor="w", padx=12, pady=(0, 12)
        )
        
    except ImportError:
        messagebox.showerror("❌ Error", "Se requiere instalar matplotlib para generar gráficos.\nEjecute: pip install matplotlib")
    except Exception as e:
        messagebox.showerror("❌ Error", f"Error al generar gráfico: {str(e)}")

def abrir_reporte(tipo, ventana_principal):
    """Calls the corresponding report function."""
    if tipo == "diario":
        generar_reporte_diario(ventana_principal)
    elif tipo == "semanal":
        generar_reporte_semanal(ventana_principal)
    elif tipo == "mensual":
        abrir_reportes_mensuales(ventana_principal)
    elif tipo == "graf_ganancia":
        generar_grafico_ventas_mensuales(ventana_principal)
    elif tipo == "graf_ventas":
        generar_grafico_ventas_mensuales(ventana_principal)
    elif tipo == "graf_categoria":
        generar_productos_mas_vendidos(ventana_principal)
    else:
        print(f"Reporte no implementado: {tipo}")

def generar_productos_mas_vendidos(ventana_principal):
    """Genera un reporte de productos más vendidos."""
    if not cursor:
        return
    
    ventana_productos = tk.Toplevel(ventana_principal)
    ventana_productos.title("Productos más vendidos · VmPOS")
    ventana_productos.configure(bg=T.BG_APP)
    ventana_productos.transient(ventana_principal)
    ventana_productos.grab_set()
    try:
        ventana_productos.minsize(640, 460)
    except (tk.TclError, Exception):
        pass
    centrar_ventana(ventana_productos, 880, 580, ventana_principal)
    _ttk_tree_theme(ventana_productos)

    root = tk.Frame(ventana_productos, bg=T.BG_APP)
    root.pack(fill=tk.BOTH, expand=True)

    hdr = tk.Frame(root, bg=T.POS_HEADER, height=72)
    hdr.pack(fill=tk.X)
    hdr.pack_propagate(False)
    hl = tk.Frame(hdr, bg=T.POS_HEADER)
    hl.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=(12, 14))
    tk.Label(hl, text="Productos más vendidos", font=F_TITLE, bg=T.POS_HEADER, fg=T.WHITE).pack(anchor="w")
    tk.Label(
        hl,
        text="Ventana móvil de 30 días · ranking por cantidad",
        font=F_SMALL,
        bg=T.POS_HEADER,
        fg=T.HEADER_TEXT_DIM,
    ).pack(anchor="w", pady=(4, 0))

    body = tk.Frame(root, bg=T.BG_APP)
    body.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

    fecha_fin = datetime.now()
    fecha_inicio = fecha_fin - timedelta(days=30)
    fecha_fin_str = fecha_fin.strftime("%Y-%m-%d")
    fecha_inicio_str = fecha_inicio.strftime("%Y-%m-%d")

    try:
        cursor.execute(
            """
            SELECT dv.nombre_producto, 
                   SUM(dv.cantidad) as total_cantidad,
                   SUM(dv.subtotal) as total_ingresos,
                   COUNT(DISTINCT v.id_venta) as num_ventas
            FROM detalle_ventas dv
            INNER JOIN ventas v ON dv.id_venta = v.id_venta
            WHERE v.fecha_venta BETWEEN ? AND ?
            GROUP BY dv.nombre_producto
            ORDER BY total_cantidad DESC
            LIMIT 20
            """,
            (fecha_inicio_str, fecha_fin_str),
        )
        
        productos_data = cursor.fetchall()
        
        if not productos_data:
            tk.Label(
                body,
                text="No hay datos de productos en los últimos 30 días.",
                font=F_BODY,
                bg=T.BG_APP,
                fg=T.TEXT_MUTED,
            ).pack(pady=40)
            return
        
        table_card = tk.Frame(body, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
        table_card.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        bar = tk.Frame(table_card, bg=T.ACCENT, height=3)
        bar.pack(fill=tk.X)
        tw_wrap = tk.Frame(table_card, bg=T.BG_CARD)
        tw_wrap.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        columnas = ("Ranking", "Producto", "Cant. vendida", "Ingresos", "Ventas")
        tabla_productos = ttk.Treeview(tw_wrap, columns=columnas, show="headings", height=14)
        tabla_productos.pack(fill=tk.BOTH, expand=True)

        widths = [72, 280, 110, 120, 90]
        for i, col in enumerate(columnas):
            tabla_productos.heading(col, text=col)
            stretch = col == "Producto"
            anc = "w" if col == "Producto" else "center"
            tabla_productos.column(col, width=widths[i], anchor=anc, stretch=stretch)

        for i, (producto, cantidad, ingresos, num_ventas) in enumerate(productos_data, 1):
            rank_txt = f"{i}."
            tabla_productos.insert(
                "",
                tk.END,
                values=(rank_txt, producto, f"{cantidad:.0f}", formato_peso(ingresos), num_ventas),
            )

        stats_frame = tk.Frame(body, bg=T.BG_SUBTLE, highlightbackground=T.BORDER, highlightthickness=1)
        stats_frame.pack(fill=tk.X)

        producto_top = productos_data[0]
        total_productos_vendidos = sum(p[1] for p in productos_data)
        total_ingresos_productos = sum(p[2] for p in productos_data)

        tk.Label(
            stats_frame,
            text="Resumen (top 20)",
            font=F_BODY_B,
            bg=T.BG_SUBTLE,
            fg=T.TEXT,
        ).pack(anchor="w", padx=12, pady=(10, 4))

        resumen = (
            f"Líder: {producto_top[0]} ({producto_top[1]:.0f} uds.)\n"
            f"Unidades en el ranking: {total_productos_vendidos:.0f}\n"
            f"Ingresos acumulados (top 20): {formato_peso(total_ingresos_productos)}"
        )

        tk.Label(
            stats_frame,
            text=resumen,
            font=F_BODY,
            bg=T.BG_SUBTLE,
            fg=T.TEXT_MUTED,
            justify="left",
        ).pack(anchor="w", padx=12, pady=(0, 12))

    except Exception as e:
        messagebox.showerror("Error", f"Error al obtener productos más vendidos: {str(e)}", parent=ventana_productos)

# 🖼️ User interface functions
def crear_cuadro(padre, texto, color_acento, tipo, icon, ventana_principal):
    """Tarjeta clickeable para abrir un tipo de reporte (tema VmPOS)."""
    frame = tk.Frame(
        padre,
        bg=T.BG_CARD,
        highlightbackground=T.BORDER,
        highlightthickness=1,
    )
    frame.pack_propagate(False)
    frame.grid_propagate(False)
    try:
        frame.configure(width=280, height=118)
    except (tk.TclError, Exception):
        pass

    card_header = tk.Frame(frame, bg=color_acento, height=4)
    card_header.pack(fill=tk.X)

    card_content = tk.Frame(frame, bg=T.BG_CARD)
    card_content.pack(fill=tk.BOTH, expand=True, padx=14, pady=(10, 12))

    tk.Label(card_content, text=icon, font=("Segoe UI Emoji", 22), bg=T.BG_CARD, fg=color_acento).pack(pady=(0, 4))
    tk.Label(card_content, text=texto, font=F_BODY_B, bg=T.BG_CARD, fg=T.TEXT).pack()

    def on_enter(_e):
        try:
            frame.configure(highlightbackground=color_acento, highlightthickness=2)
            card_content.configure(bg=T.BG_SUBTLE)
            for ch in card_content.winfo_children():
                if isinstance(ch, tk.Label):
                    ch.configure(bg=T.BG_SUBTLE)
        except (tk.TclError, Exception):
            pass

    def on_leave(_e):
        try:
            frame.configure(highlightbackground=T.BORDER, highlightthickness=1)
            card_content.configure(bg=T.BG_CARD)
            for ch in card_content.winfo_children():
                if isinstance(ch, tk.Label):
                    ch.configure(bg=T.BG_CARD)
        except (tk.TclError, Exception):
            pass

    def on_press(_e):
        try:
            frame.configure(highlightbackground=T.ACCENT, highlightthickness=2)
        except (tk.TclError, Exception):
            pass

    def on_release(e):
        on_leave(e)
        try:
            w = frame.winfo_containing(e.x_root, e.y_root)
            while w:
                if w == frame:
                    abrir_reporte(tipo, ventana_principal)
                    break
                w = w.master
        except (tk.TclError, Exception):
            pass

    frame.bind("<Enter>", on_enter)
    frame.bind("<Leave>", on_leave)
    frame.bind("<ButtonPress-1>", on_press)
    frame.bind("<ButtonRelease-1>", on_release)
    frame.configure(cursor="hand2")
    
    for child in frame.winfo_children():
        if isinstance(child, tk.Frame):
            child.bind("<Enter>", on_enter)
            child.bind("<Leave>", on_leave)
            child.bind("<ButtonPress-1>", on_press)
            child.bind("<ButtonRelease-1>", on_release)
            child.configure(cursor="hand2")
            for widget in child.winfo_children():
                widget.bind("<Enter>", on_enter)
                widget.bind("<Leave>", on_leave)
                widget.bind("<ButtonPress-1>", on_press)
                widget.bind("<ButtonRelease-1>", on_release)
                try:
                    widget.configure(cursor="hand2")
                except (tk.TclError, Exception):
                    pass

    return frame

def iniciar_reportes(parent=None):
    """Inicializa la ventana principal de reportes."""
    global conn, cursor
    crear_tabla_reportes_si_no_existe()
    if not conectar_db():
        if parent is not None:
            try:
                parent.wm_deiconify()
                parent.lift()
                parent.focus_force()
            except tk.TclError:
                pass
        return
        
    if parent is not None:
        ventana_principal = tk.Toplevel(parent)
        try:
            ventana_principal.transient(parent)
        except tk.TclError:
            pass
    else:
        ventana_principal = tk.Tk()
    ventana_principal.title("Reportes · VmPOS")
    if parent is not None:
        from navegacion_ventanas import instalar_barra_volver

        instalar_barra_volver(ventana_principal, parent)
    else:
        from layout_responsive import configurar_ventana_modulo

        configurar_ventana_modulo(ventana_principal, min_w=920, min_h=540)
    ventana_principal.resizable(True, True)
    ventana_principal.configure(bg=T.BG_APP)
    ventana_principal.protocol("WM_DELETE_WINDOW", lambda: cerrar_app(ventana_principal))
    ventana_principal.update_idletasks()

    footer_frame = tk.Frame(ventana_principal, bg=T.FOOTER, height=40)
    footer_frame.pack_propagate(False)
    footer_frame.pack(side=tk.BOTTOM, fill=tk.X)
    tk.Label(
        footer_frame,
        text="VmPOS · reportes y análisis",
        font=F_SMALL,
        bg=T.FOOTER,
        fg=T.HEADER_TEXT_DIM,
    ).pack(expand=True)

    cuerpo = crear_cuerpo_modulo_scroll(ventana_principal, bg=T.BG_APP)

    header_frame = tk.Frame(cuerpo, bg=T.POS_HEADER, height=78)
    header_frame.pack(fill=tk.X)
    header_frame.pack_propagate(False)
    header_left = tk.Frame(header_frame, bg=T.POS_HEADER)
    header_left.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=12)
    tk.Label(
        header_left, text="Reportes", font=F_TITLE, bg=T.POS_HEADER, fg=T.WHITE, anchor="w"
    ).pack(anchor="w")
    tk.Label(
        header_left,
        text="Periodos, gráficos y exportación (PDF / Excel)",
        font=F_SMALL,
        bg=T.POS_HEADER,
        fg=T.HEADER_TEXT_DIM,
        anchor="w",
    ).pack(anchor="w", pady=(2, 0))
    header_right = tk.Frame(header_frame, bg=T.POS_HEADER)
    header_right.pack(side=tk.RIGHT, padx=20, pady=12)
    lbl_fecha_rep = tk.Label(
        header_right, text="", font=F_SMALL, bg=T.POS_HEADER, fg=T.HEADER_TEXT_DIM, anchor="e"
    )
    lbl_fecha_rep.pack(anchor="e")
    lbl_hora_rep = tk.Label(
        header_right, text="", font=F_SMALL, bg=T.POS_HEADER, fg=T.WHITE, anchor="e"
    )
    lbl_hora_rep.pack(anchor="e")

    def actualizar_tiempo_rep():
        ahora = datetime.now()
        lbl_fecha_rep.config(text=ahora.strftime("%d %b %Y"))
        lbl_hora_rep.config(text=ahora.strftime("%H:%M:%S"))
        ventana_principal.after(1000, actualizar_tiempo_rep)

    actualizar_tiempo_rep()

    main_content = tk.Frame(cuerpo, bg=T.BG_APP)
    main_content.pack(fill=tk.BOTH, expand=True, padx=16, pady=14)

    tk.Label(main_content, text="Elegir reporte", font=F_HEAD, bg=T.BG_APP, fg=T.TEXT).pack(
        anchor="w", pady=(0, 4)
    )
    tk.Label(
        main_content,
        text="Toca una tarjeta para abrir el detalle o el historial.",
        font=F_SMALL,
        bg=T.BG_APP,
        fg=T.TEXT_MUTED,
    ).pack(anchor="w", pady=(0, 14))

    panel_wrap = tk.Frame(main_content, bg=T.BG_APP)
    panel_wrap.pack(fill=tk.BOTH, expand=True)
    panel = tk.Frame(panel_wrap, bg=T.BG_APP)
    panel.pack(fill=tk.BOTH, expand=True)

    opciones = [
        ("Reporte diario", T.STAT_4, "diario", "☀️"),
        ("Reporte semanal", T.STAT_1, "semanal", "🗓️"),
        ("Reportes mensuales", T.STAT_2, "mensual", "📁"),
        ("Análisis de ventas", T.STAT_3, "graf_ganancia", "📊"),
        ("Gráfico de ventas", T.ACCENT, "graf_ventas", "📈"),
        ("Productos más vendidos", T.STAT_4, "graf_categoria", "📦"),
    ]

    cuadros_reporte = []
    for texto, color, tipo, icon in opciones:
        cuadro = crear_cuadro(panel, texto, color, tipo, icon, ventana_principal)
        cuadros_reporte.append(cuadro)

    bind_reflow_grid_uniform(panel, cuadros_reporte, columnas_cuando_anchas=3, umbral=780, pad_exterior=16)

    modulo_scroll_finalizar(cuerpo)

    if parent is None:
        ventana_principal.mainloop()

if __name__ == "__main__":
    iniciar_reportes()