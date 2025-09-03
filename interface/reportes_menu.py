import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
import sys
from datetime import datetime, timedelta
import calendar
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
        
        if not tabla_ventas:
            # Crear tabla ventas
            cursor.execute("""
                CREATE TABLE ventas (
                    id_venta INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha_venta DATE NOT NULL,
                    hora_venta TIME NOT NULL,
                    total_venta REAL NOT NULL,
                    cliente_id INTEGER,
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Tabla 'ventas' creada")
        
        # Verificar si existe la tabla detalle_ventas
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='detalle_ventas'
        """)
        tabla_detalle = cursor.fetchone()
        
        if not tabla_detalle:
            # Crear tabla detalle_ventas
            cursor.execute("""
                CREATE TABLE detalle_ventas (
                    id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_venta INTEGER NOT NULL,
                    nombre_producto TEXT NOT NULL,
                    cantidad INTEGER NOT NULL,
                    precio_unitario REAL NOT NULL,
                    subtotal REAL NOT NULL,
                    FOREIGN KEY (id_venta) REFERENCES ventas (id_venta)
                )
            """)
            print("✅ Tabla 'detalle_ventas' creada")
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"❌ Error verificando/creando tablas: {e}")
        if conn:
            conn.rollback()
        return False

# Configuración de rutas para PyInstaller
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Importaciones opcionales con manejo de errores
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
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

# ⚠️ The path to the database
# Configuración de rutas mejorada para PyInstaller
if getattr(sys, 'frozen', False):
    # Si está ejecutándose como ejecutable
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Si está ejecutándose como script de Python
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ruta de base de datos - siempre fuera del ejecutable para persistencia
base_dir = BASE_DIR
database_dir = os.path.join(base_dir, 'database')
ruta_db = os.path.join(database_dir, 'ventas.db')

# Crear directorio si no existe
if not os.path.exists(database_dir):
    os.makedirs(database_dir, exist_ok=True)
# ⚠️ The folder to save PDFs and Excel files
pdf_dir = os.path.join(base_dir, '..', 'reports_pdf')
excel_dir = os.path.join(base_dir, '..', 'reports_excel')
if not os.path.exists(pdf_dir):
    os.makedirs(pdf_dir)
if not os.path.exists(excel_dir):
    os.makedirs(excel_dir)

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
    except:
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

# 📊 Report Functions
def generar_reporte_diario(ventana_principal):
    """Prepares and displays the daily sales report."""
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    abrir_reporte_detallado(ventana_principal, "Reporte Diario", fecha_actual, fecha_actual)

def generar_reporte_semanal(ventana_principal):
    """Prepares and displays the weekly sales report."""
    fecha_fin = datetime.now()
    fecha_inicio = fecha_fin - timedelta(days=7)
    fecha_fin_str = fecha_fin.strftime("%Y-%m-%d")
    fecha_inicio_str = fecha_inicio.strftime("%Y-%m-%d")
    abrir_reporte_detallado(ventana_principal, "Reporte Semanal", fecha_inicio_str, fecha_fin_str)

def abrir_reporte_detallado(ventana_principal, titulo, fecha_inicio_str, fecha_fin_str):
    """Opens a window with a detailed sales table for a given period with expenses included."""
    if not cursor: return
    
    ventana_reporte = tk.Toplevel(ventana_principal)
    ventana_reporte.title(f"📊 {titulo}")
    ventana_reporte.geometry("1200x700")
    ventana_reporte.configure(bg="#ff9ff3")
    ventana_reporte.transient(ventana_principal)
    ventana_reporte.grab_set()
    
    # Frame principal con scroll
    main_frame = tk.Frame(ventana_reporte, bg="#ff9ff3")
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    tk.Label(main_frame, text=f"📊 {titulo.upper()} ({fecha_inicio_str} a {fecha_fin_str})",
             font=("Segoe UI", 16, "bold"), bg="#ff9ff3", fg="#e84393").pack(pady=10)

    # Frame para las tablas (lado a lado)
    tablas_frame = tk.Frame(main_frame, bg="#ff9ff3")
    tablas_frame.pack(fill="both", expand=True, pady=10)

    # TABLA DE VENTAS (Izquierda)
    ventas_frame = tk.Frame(tablas_frame, bg="white", relief="raised", bd=2)
    ventas_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

    tk.Label(ventas_frame, text="💰 VENTAS DEL PERÍODO", font=("Segoe UI", 12, "bold"), 
             bg="#4CAF50", fg="white").pack(fill="x", pady=5)

    columnas_ventas = ("Fecha", "Hora", "Producto", "Cant.", "P. Unit.", "Subtotal")
    tabla_ventas = ttk.Treeview(ventas_frame, columns=columnas_ventas, show="headings", height=15)
    tabla_ventas.pack(fill="both", expand=True, padx=5, pady=5)

    # Configurar columnas de ventas
    widths_ventas = [80, 60, 180, 50, 80, 100]
    for i, col in enumerate(columnas_ventas):
        tabla_ventas.heading(col, text=col)
        tabla_ventas.column(col, width=widths_ventas[i], anchor="center")

    # TABLA DE GASTOS (Derecha)
    gastos_frame = tk.Frame(tablas_frame, bg="white", relief="raised", bd=2)
    gastos_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))

    tk.Label(gastos_frame, text="💸 GASTOS DEL PERÍODO", font=("Segoe UI", 12, "bold"), 
             bg="#FF5722", fg="white").pack(fill="x", pady=5)

    columnas_gastos = ("Fecha", "Hora", "Concepto", "Valor")
    tabla_gastos = ttk.Treeview(gastos_frame, columns=columnas_gastos, show="headings", height=15)
    tabla_gastos.pack(fill="both", expand=True, padx=5, pady=5)

    # Configurar columnas de gastos
    widths_gastos = [80, 60, 200, 100]
    for i, col in enumerate(columnas_gastos):
        tabla_gastos.heading(col, text=col)
        tabla_gastos.column(col, width=widths_gastos[i], anchor="center")

    # Obtener y mostrar datos de VENTAS
    # Obtener y mostrar datos de VENTAS - VERSIÓN SEGURA
    total_ventas_periodo = 0
    try:
        # Primero verificar qué tablas existen
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('ventas', 'detalle_ventas')
        """)
        tablas_existentes = [row[0] for row in cursor.fetchall()]
    
        if 'ventas' not in tablas_existentes:
            ventas_periodo = []
        elif 'detalle_ventas' not in tablas_existentes:
            # Solo tabla ventas existe
            cursor.execute("""
                SELECT fecha_venta, hora_venta, 'Venta General' as producto, 1 as cantidad, total_venta, total_venta
                FROM ventas
                WHERE fecha_venta BETWEEN ? AND ?
                ORDER BY fecha_venta DESC, hora_venta DESC
            """, (fecha_inicio_str, fecha_fin_str))
            ventas_periodo = cursor.fetchall()
        else:
        # Ambas tablas existen, usar LEFT JOIN por seguridad
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
            tabla_ventas.insert("", tk.END, values=(
                venta[0], venta[1], venta[2], venta[3], 
                formato_peso(venta[4]), formato_peso(venta[5])
            ))
            total_ventas_periodo += venta[5]

    except Exception as e:
        messagebox.showerror("❌ Error al cargar ventas", str(e))

    # Obtener y mostrar datos de GASTOS
    total_gastos_periodo = 0
    gastos_periodo = obtener_gastos_periodo(fecha_inicio_str, fecha_fin_str)
    
    for gasto in gastos_periodo:
        tabla_gastos.insert("", tk.END, values=(
            gasto[2], gasto[3], gasto[0], formato_peso(gasto[1])
        ))
        total_gastos_periodo += gasto[1]

    # RESUMEN FINANCIERO
    resumen_frame = tk.Frame(main_frame, bg="#E3F2FD", relief="raised", bd=2)
    resumen_frame.pack(fill="x", pady=20)

    tk.Label(resumen_frame, text="📈 RESUMEN FINANCIERO", font=("Segoe UI", 14, "bold"), 
             bg="#E3F2FD", fg="#1976D2").pack(pady=10)

    resumen_content = tk.Frame(resumen_frame, bg="#E3F2FD")
    resumen_content.pack(pady=10)

    # Calcular ganancia neta
    ganancia_neta = total_ventas_periodo - total_gastos_periodo

    resumen_data = [
        ("💰 Total Ventas:", formato_peso(total_ventas_periodo), "#4CAF50"),
        ("💸 Total Gastos:", formato_peso(total_gastos_periodo), "#FF5722"),
        ("📊 Ganancia Neta:", formato_peso(ganancia_neta), "#2196F3" if ganancia_neta >= 0 else "#F44336")
    ]

    for i, (label, valor, color) in enumerate(resumen_data):
        item_frame = tk.Frame(resumen_content, bg="#E3F2FD")
        item_frame.pack(fill="x", padx=20, pady=5)
        
        tk.Label(item_frame, text=label, font=("Segoe UI", 12, "bold"), 
                bg="#E3F2FD", fg="#333").pack(side="left")
        tk.Label(item_frame, text=valor, font=("Segoe UI", 12, "bold"), 
                bg="#E3F2FD", fg=color).pack(side="right")

def generar_reporte_mensual_pdf():
    """Generates a monthly report and creates a PDF with expenses included."""
    if not REPORTLAB_DISPONIBLE:
        messagebox.showerror("❌ Error", "ReportLab no está disponible. No se pueden generar reportes PDF.")
        return
        
    if not cursor: return
    try:
        # Calcular fechas del mes actual
        hoy = datetime.now()
        ultimo_dia = calendar.monthrange(hoy.year, hoy.month)[1]
        fecha_inicio_str = hoy.replace(day=1).strftime("%Y-%m-%d")
        fecha_fin_str = hoy.replace(day=ultimo_dia).strftime("%Y-%m-%d")

        # Obtener datos de ventas
        cursor.execute("""
            SELECT v.fecha_venta, v.hora_venta, v.total_venta
            FROM ventas v
            WHERE v.fecha_venta BETWEEN ? AND ?
            ORDER BY v.fecha_venta DESC
        """, (fecha_inicio_str, fecha_fin_str))
        ventas_mes = cursor.fetchall()
        
        cursor.execute("""
            SELECT SUM(total_venta) FROM ventas
            WHERE fecha_venta BETWEEN ? AND ?
        """, (fecha_inicio_str, fecha_fin_str))
        total_ventas = cursor.fetchone()[0] or 0

        # Obtener datos de gastos
        gastos_mes = obtener_gastos_periodo(fecha_inicio_str, fecha_fin_str)
        total_gastos = sum(gasto[1] for gasto in gastos_mes)
        
        # Calcular ganancia neta
        ganancia_neta = total_ventas - total_gastos
        
        # Crear PDF
        pdf_path = os.path.join(pdf_dir, f"Reporte_Mensual_Completo_{hoy.strftime('%Y-%m')}.pdf")
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        story = []
        
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Heading1', fontSize=18, fontName='Helvetica-Bold'))
        styles.add(ParagraphStyle(name='Normal', fontSize=10))

        story.append(Paragraph("Reporte Financiero Mensual Completo", styles['Heading1']))
        story.append(Paragraph(f"Periodo: {fecha_inicio_str} a {fecha_fin_str}", styles['Normal']))
        story.append(Spacer(1, 0.2 * inch))

        # Resumen ejecutivo
        story.append(Paragraph("<b>RESUMEN EJECUTIVO</b>", styles['Normal']))
        story.append(Paragraph(f"<b>Total de Ventas:</b> {formato_peso(total_ventas)}", styles['Normal']))
        story.append(Paragraph(f"<b>Total de Gastos:</b> {formato_peso(total_gastos)}", styles['Normal']))
        story.append(Paragraph(f"<b>Ganancia Neta:</b> {formato_peso(ganancia_neta)}", styles['Normal']))
        story.append(Spacer(1, 0.3 * inch))

        # Tabla de ventas
        story.append(Paragraph("<b>DETALLE DE VENTAS</b>", styles['Normal']))
        data_ventas = [["Fecha", "Hora", "Total Venta"]]
        for venta in ventas_mes:
            data_ventas.append([venta[0], venta[1], formato_peso(venta[2])])

        if len(data_ventas) > 1:
            table_ventas = Table(data_ventas, colWidths=[2.5*inch, 2*inch, 2.5*inch])
            table_ventas.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#E8F5E8')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#4CAF50'))
            ]))
            story.append(table_ventas)
        
        story.append(Spacer(1, 0.3 * inch))

        # Tabla de gastos
        story.append(Paragraph("<b>DETALLE DE GASTOS</b>", styles['Normal']))
        data_gastos = [["Fecha", "Concepto", "Valor"]]
        for gasto in gastos_mes:
            data_gastos.append([gasto[2], gasto[0], formato_peso(gasto[1])])

        if len(data_gastos) > 1:
            table_gastos = Table(data_gastos, colWidths=[2*inch, 3.5*inch, 2.5*inch])
            table_gastos.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF5722')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FFE8E0')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#FF5722'))
            ]))
            story.append(table_gastos)
        else:
            story.append(Paragraph("No hay gastos registrados en este periodo.", styles['Normal']))

        doc.build(story)

        # Guardar en la base de datos
        resumen = f"Ventas: {formato_peso(total_ventas)} | Gastos: {formato_peso(total_gastos)} | Ganancia: {formato_peso(ganancia_neta)}"
        cursor.execute("""
            INSERT INTO reportes (tipo, fecha_inicio, fecha_fin, resumen, ruta_pdf)
            VALUES (?, ?, ?, ?, ?)
        """, ('mensual', fecha_inicio_str, fecha_fin_str, resumen, pdf_path))
        conn.commit()

        messagebox.showinfo("✅ Reporte Mensual", f"Reporte mensual completo generado exitosamente.\n\n{resumen}")
        
    except Exception as e:
        messagebox.showerror("❌ Error al generar reporte", f"Error: {str(e)}")
        conn.rollback()

def generar_excel_mensual():
    """Genera un archivo Excel con el reporte mensual detallado."""
    if not OPENPYXL_DISPONIBLE:
        messagebox.showerror("❌ Error", "OpenPyXL no está disponible. No se pueden generar reportes Excel.")
        return
        
    if not cursor: return
    
    try:
        # Calcular fechas del mes actual
        hoy = datetime.now()
        ultimo_dia = calendar.monthrange(hoy.year, hoy.month)[1]
        fecha_inicio_str = hoy.replace(day=1).strftime("%Y-%m-%d")
        fecha_fin_str = hoy.replace(day=ultimo_dia).strftime("%Y-%m-%d")

        # Crear el archivo Excel
        excel_path = os.path.join(excel_dir, f"Reporte_Mensual_{hoy.strftime('%Y-%m')}.xlsx")
        wb = Workbook()
        
        # Eliminar hoja por defecto
        wb.remove(wb.active)
        
        # === HOJA 1: RESUMEN EJECUTIVO ===
        ws_resumen = wb.create_sheet("Resumen Ejecutivo")
        
        # Estilos
        header_font = Font(size=16, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="2E7D32", end_color="2E7D32", fill_type="solid")
        subheader_font = Font(size=12, bold=True)
        border = Border(left=Side(style='thin'), right=Side(style='thin'), 
                       top=Side(style='thin'), bottom=Side(style='thin'))
        
        # Título
        ws_resumen.merge_cells('A1:E1')
        ws_resumen['A1'] = f"REPORTE FINANCIERO MENSUAL - {hoy.strftime('%B %Y').upper()}"
        ws_resumen['A1'].font = header_font
        ws_resumen['A1'].fill = header_fill
        ws_resumen['A1'].alignment = Alignment(horizontal='center')
        
        # Obtener datos
        cursor.execute("SELECT SUM(total_venta) FROM ventas WHERE fecha_venta BETWEEN ? AND ?", 
                      (fecha_inicio_str, fecha_fin_str))
        total_ventas = cursor.fetchone()[0] or 0
        
        gastos_mes = obtener_gastos_periodo(fecha_inicio_str, fecha_fin_str)
        total_gastos = sum(gasto[1] for gasto in gastos_mes)
        ganancia_neta = total_ventas - total_gastos
        
        # Resumen
        ws_resumen['A3'] = "CONCEPTO"
        ws_resumen['B3'] = "VALOR"
        ws_resumen['A3'].font = subheader_font
        ws_resumen['B3'].font = subheader_font
        
        resumen_data = [
            ("Total Ventas", total_ventas),
            ("Total Gastos", total_gastos),
            ("Ganancia Neta", ganancia_neta)
        ]
        
        for i, (concepto, valor) in enumerate(resumen_data, 4):
            ws_resumen[f'A{i}'] = concepto
            ws_resumen[f'B{i}'] = valor
            ws_resumen[f'B{i}'].number_format = '$#,##0'
        
        # === HOJA 2: DETALLE DE VENTAS ===
        ws_ventas = wb.create_sheet("Detalle Ventas")
        
        headers_ventas = ["Fecha", "Hora", "Producto", "Cantidad", "Precio Unitario", "Subtotal"]
        for col, header in enumerate(headers_ventas, 1):
            cell = ws_ventas.cell(row=1, column=col, value=header)
            cell.font = subheader_font
            cell.fill = PatternFill(start_color="4CAF50", end_color="4CAF50", fill_type="solid")
            cell.font = Font(color="FFFFFF", bold=True)
        
        # Obtener datos de ventas detalladas
        cursor.execute("""
            SELECT v.fecha_venta, v.hora_venta, dv.nombre_producto, dv.cantidad, dv.precio_unitario, dv.subtotal
            FROM detalle_ventas dv
            INNER JOIN ventas v ON dv.id_venta = v.id_venta
            WHERE v.fecha_venta BETWEEN ? AND ?
            ORDER BY v.fecha_venta DESC, v.hora_venta DESC
        """, (fecha_inicio_str, fecha_fin_str))
        
        ventas_detalle = cursor.fetchall()
        
        for row, venta in enumerate(ventas_detalle, 2):
            ws_ventas.cell(row=row, column=1, value=venta[0])
            ws_ventas.cell(row=row, column=2, value=venta[1])
            ws_ventas.cell(row=row, column=3, value=venta[2])
            ws_ventas.cell(row=row, column=4, value=venta[3])
            ws_ventas.cell(row=row, column=5, value=venta[4]).number_format = '$#,##0'
            ws_ventas.cell(row=row, column=6, value=venta[5]).number_format = '$#,##0'
        
        # === HOJA 3: DETALLE DE GASTOS ===
        ws_gastos = wb.create_sheet("Detalle Gastos")
        
        headers_gastos = ["Fecha", "Hora", "Concepto", "Valor"]
        for col, header in enumerate(headers_gastos, 1):
            cell = ws_gastos.cell(row=1, column=col, value=header)
            cell.font = subheader_font
            cell.fill = PatternFill(start_color="FF5722", end_color="FF5722", fill_type="solid")
            cell.font = Font(color="FFFFFF", bold=True)
        
        for row, gasto in enumerate(gastos_mes, 2):
            ws_gastos.cell(row=row, column=1, value=gasto[2])  # fecha
            ws_gastos.cell(row=row, column=2, value=gasto[3])  # hora
            ws_gastos.cell(row=row, column=3, value=gasto[0])  # concepto
            ws_gastos.cell(row=row, column=4, value=gasto[1]).number_format = '$#,##0'  # valor
        
        # === HOJA 4: ANÁLISIS MENSUAL HISTÓRICO ===
        ws_historico = wb.create_sheet("Análisis Histórico")
        
        # Headers
        headers_historico = ["Mes/Año", "Total Ventas", "Total Gastos", "Ganancia Neta"]
        for col, header in enumerate(headers_historico, 1):
            cell = ws_historico.cell(row=1, column=col, value=header)
            cell.font = subheader_font
            cell.fill = PatternFill(start_color="2196F3", end_color="2196F3", fill_type="solid")
            cell.font = Font(color="FFFFFF", bold=True)
        
        # Obtener datos históricos de los últimos 12 meses
        fecha_hace_12_meses = hoy - timedelta(days=365)
        
        cursor.execute("""
            SELECT strftime('%Y-%m', fecha_venta) as mes, SUM(total_venta) as total_ventas
            FROM ventas
            WHERE fecha_venta >= ?
            GROUP BY strftime('%Y-%m', fecha_venta)
            ORDER BY mes DESC
        """, (fecha_hace_12_meses.strftime("%Y-%m-%d"),))
        
        ventas_historicas = cursor.fetchall()
        
        # Para cada mes, obtener también los gastos
        row = 2
        for mes_venta in ventas_historicas:
            mes_año = mes_venta[0]
            ventas_mes = mes_venta[1]
            
            # Calcular gastos del mes
            # Nota: Esta consulta es aproximada porque los gastos se almacenan en formato DD-MM-YYYY
            cursor.execute("""
                SELECT SUM(valor) FROM gastos
                WHERE substr(fecha, 7, 4) || '-' || 
                      case when length(substr(fecha, 4, 2)) = 1 then '0' || substr(fecha, 4, 2) else substr(fecha, 4, 2) end
                      = ?
            """, (mes_año,))
            
            result = cursor.fetchone()
            gastos_mes_valor = result[0] if result and result[0] else 0
            
            ganancia_mes = ventas_mes - gastos_mes_valor
            
            # Convertir mes_año a formato legible
            fecha_mes = datetime.strptime(mes_año + "-01", "%Y-%m-%d")
            mes_legible = fecha_mes.strftime("%B %Y")
            
            ws_historico.cell(row=row, column=1, value=mes_legible)
            ws_historico.cell(row=row, column=2, value=ventas_mes).number_format = '$#,##0'
            ws_historico.cell(row=row, column=3, value=gastos_mes_valor).number_format = '$#,##0'
            ws_historico.cell(row=row, column=4, value=ganancia_mes).number_format = '$#,##0'
            
            row += 1
        
        # Ajustar ancho de columnas
        for ws in [ws_resumen, ws_ventas, ws_gastos, ws_historico]:
            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                ws.column_dimensions[column_letter].width = max_length + 2
        
        # Guardar archivo
        wb.save(excel_path)
        
        messagebox.showinfo("✅ Excel Generado", 
                           f"Archivo Excel generado exitosamente:\n{excel_path}")
        
        # Abrir el archivo
        os.startfile(excel_path)
        
    except Exception as e:
        messagebox.showerror("❌ Error", f"Error al generar Excel: {str(e)}")

def abrir_reportes_mensuales(ventana_principal):
    """Opens a window to view and download monthly reports."""
    if not cursor: return
    
    ventana_mensual = tk.Toplevel(ventana_principal)
    ventana_mensual.title("📁 Reportes Mensuales")
    ventana_mensual.geometry("900x600")
    ventana_mensual.configure(bg="#ff9ff3")
    ventana_mensual.transient(ventana_principal)
    ventana_mensual.grab_set()
    
    frame_mensual = tk.Frame(ventana_mensual, bg="#ff9ff3")
    frame_mensual.pack(fill="both", expand=True, padx=20, pady=20)
    
    tk.Label(frame_mensual, text="📊 HISTORIAL DE REPORTES MENSUALES",
             font=("Segoe UI", 16, "bold"), bg="#ff9ff3", fg="#e84393").pack(pady=10)

    # Reports table
    tabla_reportes = ttk.Treeview(frame_mensual, columns=("ID", "Fecha Inicio", "Fecha Fin", "Resumen"), show="headings")
    tabla_reportes.pack(fill="both", expand=True)

    tabla_reportes.heading("ID", text="ID")
    tabla_reportes.heading("Fecha Inicio", text="Fecha de Inicio")
    tabla_reportes.heading("Fecha Fin", text="Fecha de Fin")
    tabla_reportes.heading("Resumen", text="Resumen")

    tabla_reportes.column("ID", width=50, anchor="center")
    tabla_reportes.column("Fecha Inicio", width=150, anchor="center")
    tabla_reportes.column("Fecha Fin", width=150, anchor="center")
    tabla_reportes.column("Resumen", width=400)

    def cargar_reportes():
        tabla_reportes.delete(*tabla_reportes.get_children())
        cursor.execute("SELECT id_reporte, fecha_inicio, fecha_fin, resumen, ruta_pdf FROM reportes WHERE tipo = 'mensual' ORDER BY fecha_inicio DESC")
        for row in cursor.fetchall():
            tabla_reportes.insert("", tk.END, values=(row[0], row[1], row[2], row[3]), tags=(row[4],))

    def descargar_pdf():
        seleccionado = tabla_reportes.focus()
        if not seleccionado:
            messagebox.showwarning("⚠️ Sin selección", "Selecciona un reporte de la lista para descargar.")
            return
        
        ruta_pdf = tabla_reportes.item(seleccionado, "tags")[0]
        if ruta_pdf and os.path.exists(ruta_pdf):
            os.startfile(ruta_pdf)
        else:
            messagebox.showerror("❌ Error", f"El archivo PDF no se encontró en la ruta:\n{ruta_pdf}")
    
    def on_double_click(event):
        descargar_pdf()

    tabla_reportes.bind("<Double-1>", on_double_click)

    botones_frame = tk.Frame(frame_mensual, bg="#ff9ff3")
    botones_frame.pack(pady=10)

    tk.Button(botones_frame, text="✨ Generar PDF Mensual",
              command=generar_reporte_mensual_pdf, bg="#a29bfe", fg="white", font=("Segoe UI", 10, "bold")).pack(side="left", padx=10)
    
    tk.Button(botones_frame, text="📊 Generar Excel Mensual",
              command=generar_excel_mensual, bg="#00b894", fg="white", font=("Segoe UI", 10, "bold")).pack(side="left", padx=10)
    
    tk.Button(botones_frame, text="⬇️ Descargar PDF",
              command=descargar_pdf, bg="#74b9ff", fg="white", font=("Segoe UI", 10, "bold")).pack(side="left", padx=10)

    cargar_reportes()

def generar_grafico_ventas_mensuales(ventana_principal):
    """Genera un gráfico de ventas mensuales históricas."""
    if not MATPLOTLIB_DISPONIBLE:
        messagebox.showerror("❌ Error", "Matplotlib no está disponible. No se pueden generar gráficos.")
        return
        
    try:
        
        # Crear ventana para el gráfico
        ventana_grafico = tk.Toplevel(ventana_principal)
        ventana_grafico.title("📈 Análisis de Ventas Mensuales")
        ventana_grafico.geometry("1000x600")
        ventana_grafico.configure(bg="#f0f0f0")
        
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
            messagebox.showinfo("📊 Sin Datos", "No hay datos suficientes para generar el gráfico.")
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
        ax1.plot(meses, ventas, marker='o', linewidth=2, markersize=8, color='#2E7D32')
        ax1.fill_between(meses, ventas, alpha=0.3, color='#4CAF50')
        ax1.set_title('Total de Ventas por Mes', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Ventas (COP)', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # Gráfico 2: Número de transacciones
        ax2.bar(meses, num_transacciones, color='#FF9800', alpha=0.8)
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
        canvas = FigureCanvasTkAgg(fig, ventana_grafico)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Frame para estadísticas adicionales
        stats_frame = tk.Frame(ventana_grafico, bg="#E3F2FD", relief="raised", bd=2)
        stats_frame.pack(fill="x", padx=20, pady=10)
        
        # Calcular estadísticas
        promedio_ventas = sum(ventas) / len(ventas)
        mes_mejor = meses[ventas.index(max(ventas))]
        mes_peor = meses[ventas.index(min(ventas))]
        
        tk.Label(stats_frame, text="📊 ESTADÍSTICAS RÁPIDAS", font=("Segoe UI", 12, "bold"), 
                bg="#E3F2FD", fg="#1976D2").pack(pady=5)
        
        stats_text = f"""
        💰 Promedio mensual: ${promedio_ventas:,.0f}
        📈 Mejor mes: {mes_mejor.strftime('%B %Y')} (${max(ventas):,.0f})
        📉 Peor mes: {mes_peor.strftime('%B %Y')} (${min(ventas):,.0f})
        📊 Total período: ${sum(ventas):,.0f}
        """
        
        tk.Label(stats_frame, text=stats_text, font=("Segoe UI", 10), 
                bg="#E3F2FD", justify="left").pack(pady=5)
        
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
    if not cursor: return
    
    ventana_productos = tk.Toplevel(ventana_principal)
    ventana_productos.title("⭐ Productos Más Vendidos")
    ventana_productos.geometry("800x600")
    ventana_productos.configure(bg="#FFF3E0")
    ventana_productos.transient(ventana_principal)
    ventana_productos.grab_set()
    
    frame_productos = tk.Frame(ventana_productos, bg="#FFF3E0")
    frame_productos.pack(fill="both", expand=True, padx=20, pady=20)
    
    tk.Label(frame_productos, text="⭐ PRODUCTOS MÁS VENDIDOS - ÚLTIMO MES",
             font=("Segoe UI", 16, "bold"), bg="#FFF3E0", fg="#E65100").pack(pady=10)

    # Obtener datos del último mes
    fecha_fin = datetime.now()
    fecha_inicio = fecha_fin - timedelta(days=30)
    fecha_fin_str = fecha_fin.strftime("%Y-%m-%d")
    fecha_inicio_str = fecha_inicio.strftime("%Y-%m-%d")

    try:
        cursor.execute("""
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
        """, (fecha_inicio_str, fecha_fin_str))
        
        productos_data = cursor.fetchall()
        
        if not productos_data:
            tk.Label(frame_productos, text="📭 No hay datos de productos en el último mes.",
                     font=("Segoe UI", 12), bg="#FFF3E0").pack(pady=50)
            return
        
        # Crear tabla
        columnas = ("Ranking", "Producto", "Cant. Vendida", "Ingresos", "Núm. Ventas")
        tabla_productos = ttk.Treeview(frame_productos, columns=columnas, show="headings", height=15)
        tabla_productos.pack(fill="both", expand=True, pady=10)

        # Configurar columnas
        widths = [80, 300, 120, 120, 100]
        for i, col in enumerate(columnas):
            tabla_productos.heading(col, text=col)
            tabla_productos.column(col, width=widths[i], anchor="center")

        # Agregar datos
        for i, (producto, cantidad, ingresos, num_ventas) in enumerate(productos_data, 1):
            # Emoji para el ranking
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}°"
            
            tabla_productos.insert("", tk.END, values=(
                emoji, producto, f"{cantidad:.0f}", formato_peso(ingresos), num_ventas
            ))

        # Estadísticas resumidas
        stats_frame = tk.Frame(frame_productos, bg="#E8F5E8", relief="raised", bd=2)
        stats_frame.pack(fill="x", pady=10)

        producto_top = productos_data[0]
        total_productos_vendidos = sum(p[1] for p in productos_data)
        total_ingresos_productos = sum(p[2] for p in productos_data)

        tk.Label(stats_frame, text="📊 RESUMEN TOP PRODUCTOS", font=("Segoe UI", 12, "bold"), 
                bg="#E8F5E8", fg="#2E7D32").pack(pady=5)

        resumen = f"""
        🥇 Producto #1: {producto_top[0]} ({producto_top[1]:.0f} unidades)
        📦 Total productos vendidos: {total_productos_vendidos:.0f} unidades
        💰 Ingresos por top productos: {formato_peso(total_ingresos_productos)}
        """

        tk.Label(stats_frame, text=resumen, font=("Segoe UI", 10), 
                bg="#E8F5E8", justify="left").pack(pady=5)

    except Exception as e:
        messagebox.showerror("❌ Error", f"Error al obtener productos más vendidos: {str(e)}")

# 🖼️ User interface functions
def crear_cuadro(padre, texto, color, tipo, icon, ventana_principal):
    """Creates an interactive box for the reports."""
    frame = tk.Frame(padre, width=280, height=120, bg="white", bd=2, relief="solid")
    frame.pack_propagate(False)
    frame.grid_propagate(False)

    card_header = tk.Frame(frame, bg=color, height=10)
    card_header.pack(fill="x")

    card_content = tk.Frame(frame, bg="white")
    card_content.pack(fill="both", expand=True, padx=10, pady=5)

    tk.Label(card_content, text=icon, font=("Segoe UI Emoji", 28), bg="white", fg=color).pack(pady=5)
    tk.Label(card_content, text=texto, font=("Segoe UI", 12, "bold"), bg="white", fg="#2d3436").pack()

    def on_enter(e):
        frame.config(relief="raised", bd=3)
    def on_leave(e):
        frame.config(relief="solid", bd=2)
    def on_press(e):
        frame.config(relief="sunken", bd=3)
    def on_release(e):
        if frame.winfo_containing(e.x_root, e.y_root) == frame:
            frame.config(relief="raised", bd=3)
        else:
            frame.config(relief="solid", bd=2)
        abrir_reporte(tipo, ventana_principal)

    frame.bind("<Enter>", on_enter)
    frame.bind("<Leave>", on_leave)
    frame.bind("<ButtonPress-1>", on_press)
    frame.bind("<ButtonRelease-1>", on_release)
    
    for child in frame.winfo_children():
        if isinstance(child, tk.Frame):
            child.bind("<Enter>", on_enter)
            child.bind("<Leave>", on_leave)
            child.bind("<ButtonPress-1>", on_press)
            child.bind("<ButtonRelease-1>", on_release)
            for widget in child.winfo_children():
                widget.bind("<Enter>", on_enter)
                widget.bind("<Leave>", on_leave)
                widget.bind("<ButtonPress-1>", on_press)
                widget.bind("<ButtonRelease-1>", on_release)

    return frame

def iniciar_reportes():
    """Initializes and runs the main reports window."""
    global conn, cursor
    crear_tabla_reportes_si_no_existe()
    if not conectar_db():
        return
        
    ventana_principal = tk.Tk()
    ventana_principal.title("REPORTES - VmPOS")
    ventana_principal.geometry("980x540")
    ventana_principal.resizable(False, False)
    ventana_principal.configure(bg="#ff9ff3")
    ventana_principal.protocol("WM_DELETE_WINDOW", lambda: cerrar_app(ventana_principal))

    # Center window
    ventana_principal.update_idletasks()
    x = (ventana_principal.winfo_screenwidth() // 2) - (980 // 2)
    y = (ventana_principal.winfo_screenheight() // 2) - (540 // 2)
    ventana_principal.geometry(f"980x540+{x}+{y}")

    # 🎨 Main header
    header_frame = tk.Frame(ventana_principal, bg="#e84393", height=80)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)

    header_left = tk.Frame(header_frame, bg="#e84393")
    header_left.pack(side="left", fill="y", padx=30)

    tk.Label(header_left, text="📊", font=("Segoe UI Emoji", 28),
            bg="#e84393", fg="white").pack(side="left", pady=15)
    tk.Label(header_left, text="REPORTES", font=("Segoe UI", 24, "bold"),
            bg="#e84393", fg="white").pack(side="left", padx=(10, 0), pady=18)
    tk.Label(header_left, text="Análisis Financiero Completo", font=("Segoe UI", 12),
            bg="#e84393", fg="#ffd3e8").pack(side="left", padx=(15, 0), pady=20)

    # 📊 Main content
    main_content = tk.Frame(ventana_principal, bg="#ffeaa7")
    main_content.pack(fill="both", expand=True, padx=20, pady=20)

    tk.Label(main_content, text="✨ SELECCIONE UN REPORTE", font=("Segoe UI", 16, "bold"),
            bg="#ffeaa7", fg="#e84393").pack(pady=20)

    panel = tk.Frame(main_content, bg="#ffeaa7")
    panel.pack(expand=True)

    # 📦 Report configuration in a 2x3 grid with icons - ACTUALIZADO
    opciones = [
        ("Reportes Diarios", "#fd79a8", "diario", "☀️"),
        ("Reportes Semanales", "#74b9ff", "semanal", "🗓️"),
        ("Reportes Mensuales", "#a29bfe", "mensual", "🌙"),
        ("Análisis de Ventas", "#55efc4", "graf_ganancia", "💰"),
        ("Gráfico de Ventas", "#ff7675", "graf_ventas", "📈"),
        ("Productos Top", "#fdcb6e", "graf_categoria", "⭐"),
    ]

    for i in range(2):
        fila = tk.Frame(panel, bg="#ffeaa7")
        fila.pack(pady=10)
        for j in range(3):
            index = i * 3 + j
            if index < len(opciones):
                texto, color, tipo, icon = opciones[index]
                cuadro = crear_cuadro(fila, texto, color, tipo, icon, ventana_principal)
                cuadro.pack(side="left", padx=15)

    # 📊 Footer with system information
    footer = tk.Frame(ventana_principal, bg="#e84393", height=50)
    footer.pack(fill="x", side="bottom")
    footer.pack_propagate(False)

    footer_left = tk.Frame(footer, bg="#e84393")
    footer_left.pack(side="left", padx=20, pady=10)

    footer_right = tk.Frame(footer, bg="#e84393")
    footer_right.pack(side="right", padx=20, pady=10)

    tk.Label(footer_left, text="📍 Puerto Colombia • 📞 +573215545788",
            font=("Segoe UI", 10), bg="#e84393", fg="white").pack()

    tk.Label(footer_right, text="✨ VmPOS v3.2.0 • Sistema Financiero Completo ✨",
            font=("Segoe UI", 10), bg="#e84393", fg="#ffd3e8").pack()

    ventana_principal.mainloop()

if __name__ == "__main__":
    iniciar_reportes()