import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import sqlite3
import os

# Configuración de la base de datos
base_dir = os.path.dirname(os.path.abspath(__file__))
database_dir = os.path.join(base_dir, '..', 'database')
ruta_db = os.path.join(database_dir, 'ventas.db')

# Conexión global a la base de datos
conn = None
cursor = None

def conectar_db():
    """Establece conexión con la base de datos"""
    global conn, cursor
    try:
        conn = sqlite3.connect(ruta_db)
        cursor = conn.cursor()
        crear_tabla_gastos()
        return True
    except Exception as e:
        messagebox.showerror("Error de conexión", f"No se pudo conectar a la base de datos:\n{e}")
        return False

def crear_tabla_gastos():
    """Crea la tabla de gastos si no existe"""
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
        messagebox.showerror("Error", f"Error al crear tabla de gastos: {e}")

def obtener_gastos():
    """Obtiene todos los gastos de la base de datos"""
    try:
        cursor.execute("SELECT * FROM gastos ORDER BY fecha_registro DESC")
        return cursor.fetchall()
    except Exception as e:
        messagebox.showerror("Error", f"Error al obtener gastos: {e}")
        return []

def agregar_gasto_db(concepto, valor, fecha, hora):
    """Agrega un gasto a la base de datos"""
    try:
        cursor.execute("""
            INSERT INTO gastos (concepto, valor, fecha, hora)
            VALUES (?, ?, ?, ?)
        """, (concepto, valor, fecha, hora))
        conn.commit()
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Error al agregar gasto: {e}")
        conn.rollback()
        return False

def eliminar_gasto_db(id_gasto):
    """Elimina un gasto de la base de datos"""
    try:
        cursor.execute("DELETE FROM gastos WHERE id_gasto = ?", (id_gasto,))
        conn.commit()
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Error al eliminar gasto: {e}")
        conn.rollback()
        return False

def modificar_gasto_db(id_gasto, concepto, valor):
    """Modifica un gasto en la base de datos"""
    try:
        cursor.execute("""
            UPDATE gastos SET concepto = ?, valor = ?
            WHERE id_gasto = ?
        """, (concepto, valor, id_gasto))
        conn.commit()
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Error al modificar gasto: {e}")
        conn.rollback()
        return False

def calcular_estadisticas_gastos():
    """Calcula estadísticas de gastos"""
    try:
        # Total de gastos
        cursor.execute("SELECT SUM(valor) FROM gastos")
        total_gastos = cursor.fetchone()[0] or 0
        
        # Gastos de hoy
        fecha_hoy = datetime.now().strftime("%d-%m-%Y")
        cursor.execute("SELECT COUNT(*), SUM(valor) FROM gastos WHERE fecha = ?", (fecha_hoy,))
        resultado = cursor.fetchone()
        gastos_hoy_count = resultado[0] or 0
        gastos_hoy_valor = resultado[1] or 0
        
        # Total de registros
        cursor.execute("SELECT COUNT(*) FROM gastos")
        total_registros = cursor.fetchone()[0] or 0
        
        return total_gastos, gastos_hoy_count, gastos_hoy_valor, total_registros
    except Exception as e:
        messagebox.showerror("Error", f"Error al calcular estadísticas: {e}")
        return 0, 0, 0, 0

def iniciar_gastos():
    if not conectar_db():
        return
        
    ventana = tk.Tk()
    ventana.title("💸 Control de Gastos - VmPOS")
    ancho_pantalla = ventana.winfo_screenwidth()
    alto_pantalla = ventana.winfo_screenheight()

    # Definir proporción deseada (por ejemplo, 80% del ancho y 75% del alto)
    ancho_ventana = int(ancho_pantalla * 0.8)
    alto_ventana = int(alto_pantalla * 0.75)

    # Calcular posición para centrar la ventana
    x = (ancho_pantalla // 2) - (ancho_ventana // 2)
    y = (alto_pantalla // 2) - (alto_ventana // 2)

    # Aplicar tamaño y posición
    ventana.geometry(f"{ancho_ventana}x{alto_ventana}+{x}+{y}")
    ventana.configure(bg="#FFE4F1")
    
    # Centrar ventana
    ventana.update_idletasks()
    x = (ventana.winfo_screenwidth() // 2) - (550)
    y = (ventana.winfo_screenheight() // 2) - (350)
    ventana.geometry(f"900x600+{x}+{y}")

    # Variables globales para los campos
    global concepto_var, valor_var, fecha_var, tabla
    concepto_var = tk.StringVar()
    valor_var = tk.StringVar()
    fecha_var = tk.StringVar(value=datetime.now().strftime("%d-%m-%Y"))

    # 🌸 Header principal
    header_frame = tk.Frame(ventana, bg="#FF1493", height=100)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)

    header_content = tk.Frame(header_frame, bg="#FF1493")
    header_content.pack(expand=True, fill="both")

    title_container = tk.Frame(header_content, bg="#FF1493")
    title_container.pack(expand=True)

    tk.Label(title_container, text="💸", font=("Segoe UI Emoji", 40), 
             bg="#FF1493", fg="white").pack(side="left", pady=25, padx=(50, 15))
    tk.Label(title_container, text="CONTROL DE GASTOS", font=("Segoe UI", 22, "bold"), 
             bg="#FF1493", fg="white").pack(side="left", pady=30)
    tk.Label(title_container, text="📊", font=("Segoe UI Emoji", 40), 
             bg="#FF1493", fg="white").pack(side="left", pady=25, padx=(15, 50))

    # 🕒 Panel de fecha y hora
    def actualizar_tiempo():
        ahora = datetime.now()
        lbl_fecha.config(text=f"📅 {ahora.strftime('%d-%m-%Y')}")
        lbl_hora.config(text=f"⏰ {ahora.strftime('%H:%M:%S')}")
        fecha_var.set(ahora.strftime("%d-%m-%Y"))
        ventana.after(1000, actualizar_tiempo)

    panel_superior = tk.Frame(ventana, bg="#FFDDEE", relief="raised", bd=2)
    panel_superior.pack(fill="x", pady=5, padx=10)

    time_container = tk.Frame(panel_superior, bg="#FFDDEE")
    time_container.pack(pady=15)

    lbl_fecha = tk.Label(time_container, text="", font=("Segoe UI", 12, "bold"), 
                        bg="#FFDDEE", fg="#C71585")
    lbl_fecha.pack(side="left", padx=20)

    tk.Label(time_container, text="✨", font=("Segoe UI Emoji", 16), 
             bg="#FFDDEE").pack(side="left", padx=10)

    lbl_hora = tk.Label(time_container, text="", font=("Segoe UI", 12, "bold"), 
                       bg="#FFDDEE", fg="#C71585")
    lbl_hora.pack(side="left", padx=20)

    actualizar_tiempo()

    # 💖 Panel de estadísticas rápidas
    stats_frame = tk.Frame(ventana, bg="#FFE4F1")
    stats_frame.pack(fill="x", pady=15, padx=10)

    stats_container = tk.Frame(stats_frame, bg="#FFE4F1")
    stats_container.pack()

    def actualizar_stats_display():
        total_gastos, gastos_hoy_count, gastos_hoy_valor, total_registros = calcular_estadisticas_gastos()
        
        # Limpiar estadísticas anteriores
        for widget in stats_container.winfo_children():
            widget.destroy()
        
        stats_data = [
            ("💰", "Total Gastos", f"${total_gastos:,.0f}", "#FF6B6B"),
            ("📅", "Gastos Hoy", f"${gastos_hoy_valor:,.0f}", "#4ECDC4"),
            ("📋", "Total Registros", str(total_registros), "#45B7D1"),
            ("🔢", "Registros Hoy", str(gastos_hoy_count), "#96CEB4")
        ]

        for i, (icono, titulo, valor, color) in enumerate(stats_data):
            card = tk.Frame(stats_container, bg="white", relief="raised", bd=2, width=200, height=100)
            card.pack(side="left", padx=15, pady=5)
            card.pack_propagate(False)

            card_header = tk.Frame(card, bg=color, height=25)
            card_header.pack(fill="x")

            card_content = tk.Frame(card, bg="white")
            card_content.pack(fill="both", expand=True, padx=10, pady=10)

            tk.Label(card_content, text=icono, font=("Segoe UI Emoji", 20), bg="white").pack()
            tk.Label(card_content, text=titulo, font=("Segoe UI", 9, "bold"), 
                    bg="white", fg="#666").pack()
            tk.Label(card_content, text=valor, font=("Segoe UI", 12, "bold"), 
                    bg="white", fg=color).pack()

    actualizar_stats_display()

    # 🎀 Panel de formulario
    form_frame = tk.Frame(ventana, bg="#FFC0CB", relief="raised", bd=2)
    form_frame.pack(fill="x", pady=15, padx=10)

    tk.Label(form_frame, text="✏️ Registrar Nuevo Gasto", font=("Segoe UI", 14, "bold"), 
             bg="#FFC0CB", fg="#8B0054").pack(pady=15)

    # Contenedor del formulario
    form_container = tk.Frame(form_frame, bg="#FFC0CB")
    form_container.pack(pady=10, padx=30)

    # Primera fila - Concepto y Valor
    row1 = tk.Frame(form_container, bg="#FFC0CB")
    row1.pack(fill="x", pady=10)

    tk.Label(row1, text="📝 Concepto:", font=("Segoe UI", 11, "bold"), 
             bg="#FFC0CB", fg="#8B0054").pack(side="left", padx=(0, 10))
    concepto_entry = tk.Entry(row1, textvariable=concepto_var, font=("Segoe UI", 11), 
                             width=25, relief="solid", bd=1)
    concepto_entry.pack(side="left", padx=(0, 30))

    tk.Label(row1, text="💰 Valor:", font=("Segoe UI", 11, "bold"), 
             bg="#FFC0CB", fg="#8B0054").pack(side="left", padx=(0, 10))
    valor_entry = tk.Entry(row1, textvariable=valor_var, font=("Segoe UI", 11), 
                          width=20, relief="solid", bd=1)
    valor_entry.pack(side="left")

    # Segunda fila - Fecha y botones
    row2 = tk.Frame(form_container, bg="#FFC0CB")
    row2.pack(fill="x", pady=15)

    tk.Label(row2, text="📅 Fecha:", font=("Segoe UI", 11, "bold"), 
             bg="#FFC0CB", fg="#8B0054").pack(side="left", padx=(0, 10))
    fecha_entry = tk.Entry(row2, textvariable=fecha_var, font=("Segoe UI", 11), 
                          width=15, state="readonly", relief="solid", bd=1)
    fecha_entry.pack(side="left", padx=(0, 50))

    # Botones de acción
    def ingresar_gasto():
        if not concepto_var.get().strip():
            messagebox.showwarning("⚠️ Campo Vacío", "💖 Por favor ingresa un concepto para el gasto")
            concepto_entry.focus()
            return
        
        try:
            valor = float(valor_var.get().replace(',', '').replace('$', ''))
            if valor <= 0:
                raise ValueError("El valor debe ser mayor a 0")
        except ValueError:
            messagebox.showwarning("⚠️ Valor Inválido", "💖 Por favor ingresa un valor numérico válido")
            valor_entry.focus()
            return

        # Agregar gasto a la base de datos
        hora_actual = datetime.now().strftime("%H:%M:%S")
        if agregar_gasto_db(concepto_var.get().strip(), valor, fecha_var.get(), hora_actual):
            # Actualizar tabla y estadísticas
            actualizar_tabla()
            actualizar_stats_display()
            
            # Limpiar campos
            concepto_var.set("")
            valor_var.set("")
            concepto_entry.focus()
            
            messagebox.showinfo("✅ Éxito", f"💎 Gasto registrado exitosamente!\n\n"
                                          f"📝 Concepto: {concepto_var.get().strip()}\n"
                                          f"💰 Valor: ${valor:,.0f}")

    def eliminar_gasto():
        seleccionado = tabla.focus()
        if not seleccionado:
            messagebox.showwarning("⚠️ Selección", "💖 Por favor selecciona un gasto para eliminar")
            return
        
        respuesta = messagebox.askyesno("🗑️ Confirmar Eliminación", 
                                       "¿Estás segura de que deseas eliminar este gasto?\n\n"
                                       "⚠️ Esta acción no se puede deshacer.")
        if respuesta:
            # Obtener ID del gasto seleccionado
            valores = tabla.item(seleccionado)["values"]
            id_gasto = valores[0]  # El ID está en la primera columna
            
            if eliminar_gasto_db(id_gasto):
                actualizar_tabla()
                actualizar_stats_display()
                messagebox.showinfo("✅ Eliminado", "💖 Gasto eliminado exitosamente")

    def modificar_gasto():
        seleccionado = tabla.focus()
        if not seleccionado:
            messagebox.showwarning("⚠️ Selección", "💖 Por favor selecciona un gasto para modificar")
            return
        
        # Obtener datos del gasto seleccionado
        valores = tabla.item(seleccionado)["values"]
        id_gasto = valores[0]
        
        # Ventana de modificación
        ventana_mod = tk.Toplevel(ventana)
        ventana_mod.title("✏️ Modificar Gasto")
        ventana_mod.geometry("450x300")
        ventana_mod.configure(bg="#FFE4F1")
        ventana_mod.resizable(False, False)
        
        # Centrar ventana
        ventana_mod.transient(ventana)
        ventana_mod.grab_set()
        
        tk.Label(ventana_mod, text="✏️ MODIFICAR GASTO", font=("Segoe UI", 16, "bold"), 
                bg="#FFE4F1", fg="#C71585").pack(pady=20)
        
        # Variables para modificación
        mod_concepto = tk.StringVar(value=valores[1])
        mod_valor = tk.StringVar(value=str(float(valores[2].replace('$', '').replace(',', ''))))
        
        # Campos de modificación
        campos_frame = tk.Frame(ventana_mod, bg="#FFE4F1")
        campos_frame.pack(pady=20, padx=30)
        
        tk.Label(campos_frame, text="📝 Concepto:", font=("Segoe UI", 11, "bold"), 
                bg="#FFE4F1", fg="#8B0054").pack(anchor="w", pady=(0, 5))
        tk.Entry(campos_frame, textvariable=mod_concepto, font=("Segoe UI", 11), 
                width=40).pack(fill="x", pady=(0, 15))
        
        tk.Label(campos_frame, text="💰 Valor:", font=("Segoe UI", 11, "bold"), 
                bg="#FFE4F1", fg="#8B0054").pack(anchor="w", pady=(0, 5))
        tk.Entry(campos_frame, textvariable=mod_valor, font=("Segoe UI", 11), 
                width=40).pack(fill="x", pady=(0, 20))
        
        def guardar_cambios():
            try:
                nuevo_valor = float(mod_valor.get().replace(',', '').replace('$', ''))
                if nuevo_valor <= 0:
                    raise ValueError("El valor debe ser mayor a 0")
                
                if modificar_gasto_db(id_gasto, mod_concepto.get().strip(), nuevo_valor):
                    actualizar_tabla()
                    actualizar_stats_display()
                    ventana_mod.destroy()
                    messagebox.showinfo("✅ Modificado", "💖 Gasto modificado exitosamente")
                
            except ValueError as e:
                messagebox.showwarning("⚠️ Error", "💖 Por favor ingresa un valor numérico válido")
        
        # Botones
        btn_frame = tk.Frame(ventana_mod, bg="#FFE4F1")
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="💾 Guardar Cambios", command=guardar_cambios,
                 bg="#32CD32", fg="white", font=("Segoe UI", 11, "bold"), 
                 padx=20, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=10)
        
        tk.Button(btn_frame, text="❌ Cancelar", command=ventana_mod.destroy,
                 bg="#FF6B6B", fg="white", font=("Segoe UI", 11, "bold"), 
                 padx=20, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=10)

    # Botones de acción
    buttons_frame = tk.Frame(row2, bg="#FFC0CB")
    buttons_frame.pack(side="right")

    btn_ingresar = tk.Button(buttons_frame, text="💎 Ingresar", command=ingresar_gasto,
                            bg="#32CD32", fg="white", font=("Segoe UI", 11, "bold"), 
                            padx=15, pady=8, relief="flat", cursor="hand2")
    btn_ingresar.pack(side="left", padx=5)

    btn_eliminar = tk.Button(buttons_frame, text="🗑️ Eliminar", command=eliminar_gasto,
                            bg="#FF6B6B", fg="white", font=("Segoe UI", 11, "bold"), 
                            padx=15, pady=8, relief="flat", cursor="hand2")
    btn_eliminar.pack(side="left", padx=5)

    btn_modificar = tk.Button(buttons_frame, text="✏️ Modificar", command=modificar_gasto,
                             bg="#4ECDC4", fg="white", font=("Segoe UI", 11, "bold"), 
                             padx=15, pady=8, relief="flat", cursor="hand2")
    btn_modificar.pack(side="left", padx=5)

    # 🔍 Panel de búsqueda
    search_frame = tk.Frame(ventana, bg="#FFE4F1")
    search_frame.pack(fill="x", pady=10, padx=10)

    search_container = tk.Frame(search_frame, bg="#FFE4F1")
    search_container.pack()

    tk.Label(search_container, text="🔍 Buscar:", font=("Segoe UI", 11, "bold"), 
             bg="#FFE4F1", fg="#C71585").pack(side="left", padx=(0, 10))
    
    search_var = tk.StringVar()
    search_entry = tk.Entry(search_container, textvariable=search_var, font=("Segoe UI", 11), 
                           width=35, relief="solid", bd=1)
    search_entry.pack(side="left", padx=(0, 10))

    def buscar_gastos():
        busqueda = search_var.get().lower()
        if not busqueda:
            actualizar_tabla()
            return
        
        # Filtrar gastos en la base de datos
        try:
            cursor.execute("""
                SELECT * FROM gastos 
                WHERE LOWER(concepto) LIKE ? OR CAST(valor AS TEXT) LIKE ? OR fecha LIKE ?
                ORDER BY fecha_registro DESC
            """, (f'%{busqueda}%', f'%{busqueda}%', f'%{busqueda}%'))
            gastos_filtrados = cursor.fetchall()
            
            tabla.delete(*tabla.get_children())
            for gasto in gastos_filtrados:
                tag = "even" if len(tabla.get_children()) % 2 == 0 else "odd"
                tabla.insert("", "end", values=(
                    gasto[0],  # id_gasto
                    gasto[1],  # concepto
                    f"${gasto[2]:,.0f}",  # valor
                    gasto[3],  # fecha
                    gasto[4]   # hora
                ), tags=(tag,))
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al buscar gastos: {e}")

    tk.Button(search_container, text="💖 Buscar", command=buscar_gastos,
             bg="#FF69B4", fg="white", font=("Segoe UI", 10, "bold"), 
             padx=15, pady=5, relief="flat", cursor="hand2").pack(side="left", padx=5)

    tk.Button(search_container, text="🔄 Mostrar Todos", command=lambda: [search_var.set(""), actualizar_tabla()],
             bg="#9370DB", fg="white", font=("Segoe UI", 10, "bold"), 
             padx=15, pady=5, relief="flat", cursor="hand2").pack(side="left", padx=5)

    # 📋 Tabla de gastos
    table_frame = tk.Frame(ventana, bg="#FFE4F1")
    table_frame.pack(fill="both", expand=True, padx=10, pady=10)

    tk.Label(table_frame, text="📋 Lista de Gastos Registrados", font=("Segoe UI", 14, "bold"), 
             bg="#FFE4F1", fg="#C71585").pack(pady=(0, 10))

    # Contenedor de tabla con scrollbars
    table_container = tk.Frame(table_frame, bg="white", relief="raised", bd=2)
    table_container.pack(fill="both", expand=True)

    # Configurar estilo de la tabla
    style = ttk.Style()
    style.configure("Gastos.Treeview", 
                   background="white",
                   foreground="#333",
                   rowheight=35,
                   fieldbackground="white")
    style.configure("Gastos.Treeview.Heading",
                   background="#FF69B4",
                   foreground="white",
                   font=('Segoe UI', 11, 'bold'))

    columnas = ("ID", "Concepto", "Valor", "Fecha", "Hora")
    tabla = ttk.Treeview(table_container, columns=columnas, show="headings", 
                        height=10, style="Gastos.Treeview")

    # Configurar columnas
    widths = [60, 300, 120, 100, 80]
    for i, col in enumerate(columnas):
        tabla.heading(col, text=col)
        tabla.column(col, width=widths[i], anchor="center")

    # Scrollbars
    v_scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=tabla.yview)
    h_scrollbar = ttk.Scrollbar(table_container, orient="horizontal", command=tabla.xview)
    tabla.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

    tabla.pack(side="left", fill="both", expand=True)
    v_scrollbar.pack(side="right", fill="y")
    h_scrollbar.pack(side="bottom", fill="x")

    def actualizar_tabla():
        # Limpiar tabla
        tabla.delete(*tabla.get_children())
        
        # Obtener gastos de la base de datos
        gastos = obtener_gastos()
        
        # Agregar gastos a la tabla
        for gasto in gastos:
            tag = "even" if len(tabla.get_children()) % 2 == 0 else "odd"
            tabla.insert("", "end", values=(
                gasto[0],  # id_gasto
                gasto[1],  # concepto
                f"${gasto[2]:,.0f}",  # valor
                gasto[3],  # fecha
                gasto[4]   # hora
            ), tags=(tag,))
        
        # Configurar colores alternos
        tabla.tag_configure("even", background="#FFF0F5")
        tabla.tag_configure("odd", background="white")

    # Cargar datos iniciales
    actualizar_tabla()

    # 🌟 Footer
    footer_frame = tk.Frame(ventana, bg="#FF1493", height=50)
    footer_frame.pack(fill="x")
    footer_frame.pack_propagate(False)

    tk.Label(footer_frame, text="💎 Control de Gastos • Base de Datos Conectada 💎", 
             font=("Segoe UI", 11, "bold"), bg="#FF1493", fg="white").pack(expand=True, pady=15)

    # Enfocar el campo concepto al inicio
    concepto_entry.focus()

    # 🎯 Eventos de teclado
    def keyboard_shortcuts(event):
        if event.state & 4:  # Ctrl presionado
            key = event.keysym.lower()
            if key == 'n':  # Ctrl+N para nuevo gasto
                concepto_entry.focus()
            elif key == 'f':  # Ctrl+F para buscar
                search_entry.focus()
            elif key == 's':  # Ctrl+S para guardar
                ingresar_gasto()

    # Vincular Enter para ingresar gasto
    def on_enter(event):
        if event.widget == valor_entry:
            ingresar_gasto()

    valor_entry.bind('<Return>', on_enter)
    concepto_entry.bind('<Return>', lambda e: valor_entry.focus())

    ventana.bind("<KeyPress>", keyboard_shortcuts)
    ventana.focus_set()

    # Cerrar conexión al cerrar ventana
    def on_closing():
        if conn:
            conn.close()
        ventana.destroy()

    ventana.protocol("WM_DELETE_WINDOW", on_closing)
    ventana.mainloop()

# Ejecutar si es llamado directamente
if __name__ == "__main__":
    iniciar_gastos()