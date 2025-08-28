import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import calendar

# ⚠️ The path to the database
base_dir = os.path.dirname(os.path.abspath(__file__))
database_dir = os.path.join(base_dir, '..', 'database')
ruta_db = os.path.join(database_dir, 'ventas.db')
# ⚠️ The folder to save PDFs
pdf_dir = os.path.join(base_dir, '..', 'reports_pdf')
if not os.path.exists(pdf_dir):
    os.makedirs(pdf_dir)

# 🔌 Single database connection
conn = None
cursor = None

def conectar_db():
    """Establishes a single connection to the database."""
    global conn, cursor
    try:
        conn = sqlite3.connect(ruta_db)
        cursor = conn.cursor()
    except Exception as e:
        messagebox.showerror("Error de conexión", f"No se pudo conectar a la base de datos:\n{e}")
        return False
    return True

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
    """Opens a window with a detailed sales table for a given period."""
    if not cursor: return
    
    ventana_reporte = tk.Toplevel(ventana_principal)
    ventana_reporte.title(f"📊 {titulo}")
    ventana_reporte.geometry("900x600")
    ventana_reporte.configure(bg="#ff9ff3")
    ventana_reporte.transient(ventana_principal)
    ventana_reporte.grab_set()
    
    frame_reporte = tk.Frame(ventana_reporte, bg="#ff9ff3")
    frame_reporte.pack(fill="both", expand=True, padx=20, pady=20)
    
    tk.Label(frame_reporte, text=f"📊 {titulo.upper()} ({fecha_inicio_str} a {fecha_fin_str})",
             font=("Segoe UI", 16, "bold"), bg="#ff9ff3", fg="#e84393").pack(pady=10)

    # Sales table
    columnas = ("Fecha", "Hora", "Producto", "Cantidad", "P. Unitario", "Subtotal")
    tabla_ventas = ttk.Treeview(frame_reporte, columns=columnas, show="headings")
    tabla_ventas.pack(fill="both", expand=True, pady=10)

    tabla_ventas.heading("Fecha", text="Fecha")
    tabla_ventas.heading("Hora", text="Hora")
    tabla_ventas.heading("Producto", text="Producto")
    tabla_ventas.heading("Cantidad", text="Cantidad", anchor="center")
    tabla_ventas.heading("P. Unitario", text="P. Unitario", anchor="center")
    tabla_ventas.heading("Subtotal", text="Subtotal", anchor="center")

    tabla_ventas.column("Fecha", width=100, anchor="center")
    tabla_ventas.column("Hora", width=80, anchor="center")
    tabla_ventas.column("Producto", width=250)
    tabla_ventas.column("Cantidad", width=80, anchor="center")
    tabla_ventas.column("P. Unitario", width=120, anchor="center")
    tabla_ventas.column("Subtotal", width=120, anchor="center")
    
    # Get data for the table
    total_ventas_periodo = 0
    try:
        cursor.execute("""
            SELECT v.fecha_venta, v.hora_venta, dv.nombre_producto, dv.cantidad, dv.precio_unitario, dv.subtotal
            FROM detalle_ventas dv
            INNER JOIN ventas v ON dv.id_venta = v.id_venta
            WHERE v.fecha_venta BETWEEN ? AND ?
            ORDER BY v.fecha_venta DESC, v.hora_venta DESC
        """, (fecha_inicio_str, fecha_fin_str))
        
        ventas_periodo = cursor.fetchall()
        
        for venta in ventas_periodo:
            tabla_ventas.insert("", tk.END, values=(
                venta[0], 
                venta[1], 
                venta[2], 
                venta[3], 
                formato_peso(venta[4]), 
                formato_peso(venta[5])
            ))
            total_ventas_periodo += venta[5]

    except Exception as e:
        messagebox.showerror("❌ Error al cargar datos", str(e))
        return

    # Summary of the total
    tk.Label(frame_reporte, text=f"Total de ventas del período: {formato_peso(total_ventas_periodo)}",
             font=("Segoe UI", 12, "bold"), bg="#ff9ff3", fg="#2d3436").pack(pady=10)


def generar_reporte_mensual_pdf():
    """Generates a monthly report and creates a PDF."""
    if not cursor: return
    try:
        # 🐛 FIX: Calculate the start and end dates of the current month here
        hoy = datetime.now()
        ultimo_dia = calendar.monthrange(hoy.year, hoy.month)[1]
        fecha_inicio_str = hoy.replace(day=1).strftime("%Y-%m-%d")
        fecha_fin_str = hoy.replace(day=ultimo_dia).strftime("%Y-%m-%d")

        # Get data for the PDF
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
        
        # 📂 Create the PDF
        pdf_path = os.path.join(pdf_dir, f"Reporte_Mensual_{hoy.strftime('%Y-%m')}.pdf")
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        story = []
        
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Heading1', fontSize=18, fontName='Helvetica-Bold'))
        styles.add(ParagraphStyle(name='Normal', fontSize=10))

        story.append(Paragraph("Reporte de Ventas Mensual", styles['Heading1']))
        story.append(Paragraph(f"Periodo: {fecha_inicio_str} a {fecha_fin_str}", styles['Normal']))
        story.append(Spacer(1, 0.2 * inch))

        story.append(Paragraph(f"<b>Total de Ventas:</b> {formato_peso(total_ventas)}", styles['Normal']))
        story.append(Spacer(1, 0.2 * inch))

        # Sales table
        data = [["Fecha", "Hora", "Total Venta"]]
        for venta in ventas_mes:
            data.append([venta[0], venta[1], formato_peso(venta[2])])

        if len(data) > 1:
            table = Table(data, colWidths=[2.5*inch, 2.5*inch, 2.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e84393')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ffeaa7')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e84393'))
            ]))
            story.append(table)
        else:
            story.append(Paragraph("No hay ventas registradas en este periodo.", styles['Normal']))

        doc.build(story)

        # Save to the database
        resumen = f"Total ventas: {formato_peso(total_ventas)}. PDF guardado en: {pdf_path}"
        cursor.execute("""
            INSERT INTO reportes (tipo, fecha_inicio, fecha_fin, resumen, ruta_pdf)
            VALUES (?, ?, ?, ?, ?)
        """, ('mensual', fecha_inicio_str, fecha_fin_str, resumen, pdf_path))
        conn.commit()

        messagebox.showinfo("✅ Reporte Mensual", f"Reporte mensual generado y PDF creado exitosamente.\n\n{resumen}")
        
    except Exception as e:
        messagebox.showerror("❌ Error al generar reporte", f"Error: {str(e)}\n\nAsegúrate de tener la librería 'reportlab' instalada (`pip install reportlab`).")
        conn.rollback()


def abrir_reportes_mensuales(ventana_principal):
    """Opens a window to view and download monthly reports."""
    if not cursor: return
    
    ventana_mensual = tk.Toplevel(ventana_principal)
    ventana_mensual.title("📁 Reportes Mensuales")
    ventana_mensual.geometry("800x500")
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
            os.startfile(ruta_pdf) # Open the file on the system
        else:
            messagebox.showerror("❌ Error", f"El archivo PDF no se encontró en la ruta:\n{ruta_pdf}")
    
    def on_double_click(event):
        descargar_pdf()

    tabla_reportes.bind("<Double-1>", on_double_click)

    botones_frame = tk.Frame(frame_mensual, bg="#ff9ff3")
    botones_frame.pack(pady=10)

    # 🐛 FIX: Now calls the function without arguments, as the function calculates the dates itself.
    tk.Button(botones_frame, text="✨ Generar Nuevo Reporte",
              command=generar_reporte_mensual_pdf, bg="#a29bfe", fg="white", font=("Segoe UI", 10, "bold")).pack(side="left", padx=10)
    
    tk.Button(botones_frame, text="⬇️ Descargar PDF",
              command=descargar_pdf, bg="#74b9ff", fg="white", font=("Segoe UI", 10, "bold")).pack(side="left", padx=10)

    cargar_reportes()

def abrir_reporte(tipo, ventana_principal):
    """Calls the corresponding report function."""
    if tipo == "diario":
        generar_reporte_diario(ventana_principal)
    elif tipo == "semanal":
        generar_reporte_semanal(ventana_principal)
    elif tipo == "mensual":
        abrir_reportes_mensuales(ventana_principal)
    else:
        print(f"Reporte no implementado: {tipo}")

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

    # 🎨 Main header (Adapted from menu_inicio.py)
    header_frame = tk.Frame(ventana_principal, bg="#e84393", height=80)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)

    header_left = tk.Frame(header_frame, bg="#e84393")
    header_left.pack(side="left", fill="y", padx=30)

    tk.Label(header_left, text="📊", font=("Segoe UI Emoji", 28),
            bg="#e84393", fg="white").pack(side="left", pady=15)
    tk.Label(header_left, text="REPORTES", font=("Segoe UI", 24, "bold"),
            bg="#e84393", fg="white").pack(side="left", padx=(10, 0), pady=18)
    tk.Label(header_left, text="Análisis de Información", font=("Segoe UI", 12),
            bg="#e84393", fg="#ffd3e8").pack(side="left", padx=(15, 0), pady=20)

    # 📊 Main content
    main_content = tk.Frame(ventana_principal, bg="#ffeaa7")
    main_content.pack(fill="both", expand=True, padx=20, pady=20)

    tk.Label(main_content, text="✨ SELECCIONE UN REPORTE", font=("Segoe UI", 16, "bold"),
            bg="#ffeaa7", fg="#e84393").pack(pady=20)

    panel = tk.Frame(main_content, bg="#ffeaa7")
    panel.pack(expand=True)

    # 📦 Report configuration in a 2x3 grid with icons
    opciones = [
        ("Reportes Diarios", "#fd79a8", "diario", "☀️"),
        ("Reportes Semanales", "#74b9ff", "semanal", "🗓️"),
        ("Reportes Mensuales", "#a29bfe", "mensual", "🌙"),
        ("Ganancia por Mes", "#55efc4", "graf_ganancia", "💰"),
        ("Ventas por Mes", "#ff7675", "graf_ventas", "📈"),
        ("Productos Más Vendidos", "#fdcb6e", "graf_categoria", "⭐"),
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

    tk.Label(footer_right, text="✨ VmPOS v3.1.0 • Sistema Activo �",
            font=("Segoe UI", 10), bg="#e84393", fg="#ffd3e8").pack()

    ventana_principal.mainloop()

if __name__ == "__main__":
    iniciar_reportes()
