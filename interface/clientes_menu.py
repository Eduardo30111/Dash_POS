import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import sqlite3
import os

def iniciar_clientes():
    ventana = tk.Tk()
    ventana.title("💎 Clientes - VmPOS")
    ventana.geometry("1000x600")
    ventana.resizable(False, False)
    ventana.configure(bg="#FFE4F1")
    
    # Centrar ventana
    ventana.update_idletasks()
    x = (ventana.winfo_screenwidth() // 2) - (500)
    y = (ventana.winfo_screenheight() // 2) - (300)
    ventana.geometry(f"1000x600+{x}+{y}")

    # 🎨 Configurar estilo femenino
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('Feminine.TLabel', 
                    background='#FFE4F1', 
                    foreground='#C71585',
                    font=('Segoe UI', 10))
    style.configure('Header.TLabel', 
                    background='#FFE4F1', 
                    foreground='#C71585', 
                    font=('Segoe UI', 16, 'bold'))
    style.configure('Feminine.TButton',
                    background='#FF69B4',
                    foreground='white',
                    font=('Segoe UI', 10, 'bold'))

    # 🌸 Header principal con gradiente
    header_frame = tk.Frame(ventana, bg="#FF1493", height=80)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)

    # Logo y título en header
    header_content = tk.Frame(header_frame, bg="#FF1493")
    header_content.pack(expand=True, fill="both")

    title_frame = tk.Frame(header_content, bg="#FF1493")
    title_frame.pack(expand=True)

    tk.Label(title_frame, text="💎", font=("Segoe UI Emoji", 32), 
             bg="#FF1493", fg="white").pack(side="left", pady=20, padx=(50, 10))
    tk.Label(title_frame, text="GESTIÓN DE CLIENTES", font=("Segoe UI", 20, "bold"), 
             bg="#FF1493", fg="white").pack(side="left", pady=25)
    tk.Label(title_frame, text="🌸", font=("Segoe UI Emoji", 32), 
             bg="#FF1493", fg="white").pack(side="left", pady=20, padx=(10, 50))

    # 🕒 Panel de fecha y hora con diseño femenino
    def actualizar_tiempo():
        ahora = datetime.now()
        lbl_fecha.config(text=f"📅 {ahora.strftime('%d-%m-%Y')}")
        lbl_hora.config(text=f"⏰ {ahora.strftime('%H:%M:%S')}")
        ventana.after(1000, actualizar_tiempo)

    panel_superior = tk.Frame(ventana, bg="#FFDDEE", relief="raised", bd=2)
    panel_superior.pack(fill="x", pady=5, padx=10)

    time_container = tk.Frame(panel_superior, bg="#FFDDEE")
    time_container.pack(pady=10)

    lbl_fecha = tk.Label(time_container, text="", font=("Segoe UI", 12, "bold"), 
                        bg="#FFDDEE", fg="#C71585")
    lbl_fecha.pack(side="left", padx=20)

    tk.Label(time_container, text="✨", font=("Segoe UI Emoji", 16), 
             bg="#FFDDEE").pack(side="left", padx=10)

    lbl_hora = tk.Label(time_container, text="", font=("Segoe UI", 12, "bold"), 
                       bg="#FFDDEE", fg="#C71585")
    lbl_hora.pack(side="left", padx=20)

    actualizar_tiempo()

    # 💖 Panel de búsqueda y filtros
    search_frame = tk.Frame(ventana, bg="#FFC0CB", relief="raised", bd=2)
    search_frame.pack(fill="x", pady=10, padx=10)

    tk.Label(search_frame, text="🔍 Buscar cliente:", font=("Segoe UI", 11, "bold"), 
             bg="#FFC0CB", fg="#8B0054").pack(side="left", padx=15, pady=10)
    
    search_var = tk.StringVar()
    search_entry = tk.Entry(search_frame, textvariable=search_var, font=("Segoe UI", 10), 
                           width=30)
    search_entry.pack(side="left", padx=10, pady=10)

    def buscar_cliente():
        termino = search_var.get().strip()
        if termino:
            cargar_datos(filtro_busqueda=termino)
        else:
            cargar_datos()

    btn_search = tk.Button(search_frame, text="💖 Buscar", bg="#FF69B4", fg="white",
                          font=("Segoe UI", 10, "bold"), padx=15, pady=5,
                          relief="flat", cursor="hand2", command=buscar_cliente)
    btn_search.pack(side="left", padx=10, pady=10)

    btn_refresh = tk.Button(search_frame, text="🔄 Actualizar", bg="#9370DB", fg="white",
                           font=("Segoe UI", 10, "bold"), padx=15, pady=5,
                           relief="flat", cursor="hand2", command=lambda: cargar_datos())
    btn_refresh.pack(side="left", padx=5, pady=10)

    # 📊 Panel de estadísticas rápidas
    stats_frame = tk.Frame(ventana, bg="#FFE4F1")
    stats_frame.pack(fill="x", pady=10, padx=10)

    stats_container = tk.Frame(stats_frame, bg="#FFE4F1")
    stats_container.pack()

    # Variables para las estadísticas
    total_clientes_var = tk.StringVar(value="0")
    compras_hoy_var = tk.StringVar(value="0")
    ventas_mes_var = tk.StringVar(value="$0")

    # Tarjetas de estadísticas
    stats_widgets = []
    
    card1 = tk.Frame(stats_container, bg="white", relief="raised", bd=2, width=200, height=100)
    card1.pack(side="left", padx=10, pady=5)
    card1.pack_propagate(False)
    card1_header = tk.Frame(card1, bg="#FF69B4", height=25)
    card1_header.pack(fill="x")
    card1_content = tk.Frame(card1, bg="white")
    card1_content.pack(fill="both", expand=True, padx=10, pady=10)
    tk.Label(card1_content, text="👥", font=("Segoe UI Emoji", 20), bg="white").pack()
    tk.Label(card1_content, text="Total Clientes", font=("Segoe UI", 9, "bold"), 
            bg="white", fg="#666").pack()
    lbl_total_clientes = tk.Label(card1_content, textvariable=total_clientes_var, 
                                 font=("Segoe UI", 12, "bold"), bg="white", fg="#FF69B4")
    lbl_total_clientes.pack()

    card2 = tk.Frame(stats_container, bg="white", relief="raised", bd=2, width=200, height=100)
    card2.pack(side="left", padx=10, pady=5)
    card2.pack_propagate(False)
    card2_header = tk.Frame(card2, bg="#20B2AA", height=25)
    card2_header.pack(fill="x")
    card2_content = tk.Frame(card2, bg="white")
    card2_content.pack(fill="both", expand=True, padx=10, pady=10)
    tk.Label(card2_content, text="🛍️", font=("Segoe UI Emoji", 20), bg="white").pack()
    tk.Label(card2_content, text="Compras Hoy", font=("Segoe UI", 9, "bold"), 
            bg="white", fg="#666").pack()
    lbl_compras_hoy = tk.Label(card2_content, textvariable=compras_hoy_var, 
                              font=("Segoe UI", 12, "bold"), bg="white", fg="#20B2AA")
    lbl_compras_hoy.pack()

    card3 = tk.Frame(stats_container, bg="white", relief="raised", bd=2, width=200, height=100)
    card3.pack(side="left", padx=10, pady=5)
    card3.pack_propagate(False)
    card3_header = tk.Frame(card3, bg="#FF6347", height=25)
    card3_header.pack(fill="x")
    card3_content = tk.Frame(card3, bg="white")
    card3_content.pack(fill="both", expand=True, padx=10, pady=10)
    tk.Label(card3_content, text="💰", font=("Segoe UI Emoji", 20), bg="white").pack()
    tk.Label(card3_content, text="Ventas del Mes", font=("Segoe UI", 9, "bold"), 
            bg="white", fg="#666").pack()
    lbl_ventas_mes = tk.Label(card3_content, textvariable=ventas_mes_var, 
                             font=("Segoe UI", 12, "bold"), bg="white", fg="#FF6347")
    lbl_ventas_mes.pack()

    # 🎀 Tabla principal con estilo femenino
    table_frame = tk.Frame(ventana, bg="#FFE4F1")
    table_frame.pack(fill="both", expand=True, padx=10, pady=10)

    tk.Label(table_frame, text="📋 Lista de Clientes", font=("Segoe UI", 14, "bold"), 
             bg="#FFE4F1", fg="#C71585").pack(pady=(0, 10))

    # Contenedor de la tabla con scrollbar
    table_container = tk.Frame(table_frame, bg="white", relief="raised", bd=2)
    table_container.pack(fill="both", expand=True)

    # Configurar Treeview con estilo
    style.configure("Feminine.Treeview", 
                   background="white",
                   foreground="#333",
                   rowheight=30,
                   fieldbackground="white")
    style.configure("Feminine.Treeview.Heading",
                   background="#FF69B4",
                   foreground="white",
                   font=('Segoe UI', 10, 'bold'))

    columnas = ("ID", "Documento", "Nombre", "Fecha", "Hora", "Total Compras")
    tabla = ttk.Treeview(table_container, columns=columnas, show="headings", 
                        height=12, style="Feminine.Treeview")

    # Configurar columnas
    widths = [60, 120, 200, 100, 80, 120]
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

    # 🗄️ Función para conectar a la base de datos
    def conectar_db():
        # Posibles ubicaciones de la base de datos
        posibles_rutas = [
            "ventas.db",  # En el directorio actual
            os.path.join(os.path.dirname(__file__), "ventas.db"),  # En el mismo directorio del archivo
            os.path.join(os.path.dirname(__file__), "..", "ventas.db"),  # Un nivel arriba
            os.path.join(os.path.dirname(__file__), "..", "..", "ventas.db"),  # Dos niveles arriba
            os.path.join(os.getcwd(), "ventas.db")  # En el directorio de trabajo actual
        ]
        
        ruta_db = None
        
        # Buscar la base de datos en las posibles ubicaciones
        for ruta in posibles_rutas:
            if os.path.exists(ruta):
                ruta_db = ruta
                break
        
        if not ruta_db:
            # Si no se encuentra, crear en el directorio del archivo
            ruta_db = os.path.join(os.path.dirname(__file__), "..", "ventas.db")
            messagebox.showwarning("Base de Datos", f"No se encontró ventas.db. Se creará en:\n{os.path.abspath(ruta_db)}")
        
        try:
            conn = sqlite3.connect(ruta_db)
            
            # Verificar si la tabla existe
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ventas'")
            
            if not cursor.fetchone():
                # Crear la tabla si no existe
                cursor.execute('''
                    CREATE TABLE ventas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        documento TEXT,
                        cliente TEXT,
                        fecha TEXT,
                        hora TEXT,
                        total REAL,
                        metodo_pago TEXT,
                        productos TEXT
                    )
                ''')
                conn.commit()
                messagebox.showinfo("Base de Datos", "Tabla 'ventas' creada exitosamente")
            
            return conn
            
        except sqlite3.Error as e:
            messagebox.showerror("Error de Base de Datos", 
                               f"Error al conectar con la base de datos:\n{e}\n\nRuta: {ruta_db}")
            return None

    # 📊 Función para actualizar estadísticas
    def actualizar_estadisticas():
        conn = conectar_db()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            
            # Verificar si la tabla existe y tiene datos
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ventas'")
            if not cursor.fetchone():
                # Tabla no existe, mostrar valores por defecto
                total_clientes_var.set("0")
                compras_hoy_var.set("0")
                ventas_mes_var.set("$0")
                return
            
            # Total de clientes únicos
            cursor.execute("SELECT COUNT(DISTINCT cliente) FROM ventas WHERE cliente IS NOT NULL AND cliente != '' AND cliente != 'Cliente Anónimo'")
            total_clientes = cursor.fetchone()[0]
            total_clientes_var.set(str(total_clientes))
            
            # Compras de hoy
            hoy = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("SELECT COUNT(*) FROM ventas WHERE fecha = ?", (hoy,))
            compras_hoy = cursor.fetchone()[0]
            compras_hoy_var.set(str(compras_hoy))
            
            # Ventas del mes actual
            mes_actual = datetime.now().strftime('%Y-%m')
            cursor.execute("SELECT SUM(total) FROM ventas WHERE fecha LIKE ?", (f"{mes_actual}%",))
            ventas_mes = cursor.fetchone()[0] or 0
            ventas_mes_var.set(f"${ventas_mes:,.0f}")
            
        except sqlite3.Error as e:
            # En caso de error, mostrar valores por defecto
            total_clientes_var.set("0")
            compras_hoy_var.set("0") 
            ventas_mes_var.set("$0")
            print(f"Error al obtener estadísticas: {e}")
        finally:
            conn.close()

    # 📁 Cargar datos desde la base de datos
    def cargar_datos(filtro_busqueda=None):
        # Limpiar tabla
        tabla.delete(*tabla.get_children())
        
        conn = conectar_db()
        if not conn:
            messagebox.showerror("Error", "No se pudo conectar a la base de datos")
            return
        
        try:
            cursor = conn.cursor()
            
            # Verificar si la tabla tiene datos
            cursor.execute("SELECT COUNT(*) FROM ventas")
            total_registros = cursor.fetchone()[0]
            
            if total_registros == 0:
                # Si no hay datos, mostrar mensaje informativo
                messagebox.showinfo("Base de Datos Vacía", 
                                   "La base de datos está vacía. Los datos aparecerán aquí cuando realices ventas.")
                actualizar_estadisticas()
                return
            
            # Consulta SQL base
            if filtro_busqueda:
                # Buscar por cliente o documento
                query = """
                SELECT id, documento, cliente, fecha, hora, total 
                FROM ventas 
                WHERE cliente LIKE ? OR documento LIKE ?
                ORDER BY fecha DESC, hora DESC
                """
                cursor.execute(query, (f"%{filtro_busqueda}%", f"%{filtro_busqueda}%"))
            else:
                # Obtener todas las ventas
                query = """
                SELECT id, documento, cliente, fecha, hora, total 
                FROM ventas 
                ORDER BY fecha DESC, hora DESC
                """
                cursor.execute(query)
            
            resultados = cursor.fetchall()
            
            # Insertar datos en la tabla
            for idx, row in enumerate(resultados):
                id_venta, documento, cliente, fecha, hora, total = row
                
                # Alternar colores de filas
                tag = "even" if idx % 2 == 0 else "odd"
                
                # Formatear datos
                documento_mostrar = documento if documento else "N/A"
                cliente_mostrar = cliente if cliente else "Cliente Anónimo"
                fecha_mostrar = fecha if fecha else "N/A"
                hora_mostrar = hora if hora else "N/A"
                total_mostrar = f"${total:,.0f}" if total else "$0"
                
                tabla.insert("", "end", values=(
                    id_venta,
                    documento_mostrar,
                    cliente_mostrar,
                    fecha_mostrar,
                    hora_mostrar,
                    total_mostrar
                ), tags=(tag,))
            
            # Configurar colores alternos
            tabla.tag_configure("even", background="#FFF0F5")
            tabla.tag_configure("odd", background="white")
            
            # Actualizar estadísticas
            actualizar_estadisticas()
            
        except sqlite3.Error as e:
            if "no such table" in str(e).lower():
                messagebox.showerror("Error de Base de Datos", 
                                   "La tabla 'ventas' no existe. Se creará automáticamente cuando realices la primera venta.")
            else:
                messagebox.showerror("Error", f"Error al cargar los datos: {e}")
        finally:
            conn.close()

    # Cargar datos al iniciar
    cargar_datos()

    # 💝 Panel de acciones con botones femeninos
    actions_frame = tk.Frame(ventana, bg="#FFE4F1")
    actions_frame.pack(fill="x", pady=10, padx=10)

    buttons_container = tk.Frame(actions_frame, bg="#FFE4F1")
    buttons_container.pack()

    def ver_historial_cliente():
        seleccion = tabla.selection()
        if not seleccion:
            messagebox.showwarning("Selección requerida", "Por favor selecciona un cliente de la tabla")
            return
        
        # Obtener datos del cliente seleccionado
        item = tabla.item(seleccion[0])
        cliente_nombre = item['values'][2]  # Nombre del cliente
        
        if cliente_nombre == "Cliente Anónimo":
            messagebox.showinfo("Sin historial", "Este cliente no tiene un nombre registrado")
            return
        
        # Crear ventana de historial
        ventana_historial = tk.Toplevel(ventana)
        ventana_historial.title(f"📊 Historial de {cliente_nombre}")
        ventana_historial.geometry("800x500")
        ventana_historial.configure(bg="#FFE4F1")
        
        # Obtener historial del cliente
        conn = conectar_db()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT fecha, hora, total, metodo_pago 
                    FROM ventas 
                    WHERE cliente = ? 
                    ORDER BY fecha DESC, hora DESC
                """, (cliente_nombre,))
                
                historial = cursor.fetchall()
                
                # Mostrar historial en una tabla
                tk.Label(ventana_historial, text=f"📋 Historial de compras - {cliente_nombre}", 
                        font=("Segoe UI", 14, "bold"), bg="#FFE4F1", fg="#C71585").pack(pady=10)
                
                frame_historial = tk.Frame(ventana_historial)
                frame_historial.pack(fill="both", expand=True, padx=20, pady=10)
                
                cols_historial = ("Fecha", "Hora", "Total", "Método de Pago")
                tabla_historial = ttk.Treeview(frame_historial, columns=cols_historial, show="headings", style="Feminine.Treeview")
                
                for col in cols_historial:
                    tabla_historial.heading(col, text=col)
                    tabla_historial.column(col, width=150, anchor="center")
                
                for registro in historial:
                    fecha, hora, total, metodo = registro
                    tabla_historial.insert("", "end", values=(
                        fecha or "N/A",
                        hora or "N/A", 
                        f"${total:,.0f}" if total else "$0",
                        metodo or "N/A"
                    ))
                
                tabla_historial.pack(fill="both", expand=True)
                
                # Total gastado
                total_gastado = sum([r[2] for r in historial if r[2]]) or 0
                tk.Label(ventana_historial, text=f"💰 Total gastado: ${total_gastado:,.0f}", 
                        font=("Segoe UI", 12, "bold"), bg="#FFE4F1", fg="#FF6347").pack(pady=10)
                
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Error al obtener el historial: {e}")
            finally:
                conn.close()

    def diagnosticar_base_datos():
        """Función para diagnosticar problemas con la base de datos"""
        ventana_diagnostico = tk.Toplevel(ventana)
        ventana_diagnostico.title("🔍 Diagnóstico de Base de Datos")
        ventana_diagnostico.geometry("600x400")
        ventana_diagnostico.configure(bg="#FFE4F1")
        
        # Texto de diagnóstico
        text_diagnostico = tk.Text(ventana_diagnostico, wrap=tk.WORD, font=("Consolas", 10))
        text_diagnostico.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Realizar diagnóstico
        resultado = "🔍 DIAGNÓSTICO DE BASE DE DATOS\n"
        resultado += "=" * 50 + "\n\n"
        
        # Buscar la base de datos
        posibles_rutas = [
            "ventas.db",
            os.path.join(os.path.dirname(__file__), "ventas.db"),
            os.path.join(os.path.dirname(__file__), "..", "ventas.db"),
            os.path.join(os.path.dirname(__file__), "..", "..", "ventas.db"),
            os.path.join(os.getcwd(), "ventas.db")
        ]
        
        ruta_encontrada = None
        resultado += "🔎 BUSCANDO BASE DE DATOS:\n"
        
        for ruta in posibles_rutas:
            ruta_absoluta = os.path.abspath(ruta)
            if os.path.exists(ruta):
                resultado += f"✅ ENCONTRADA: {ruta_absoluta}\n"
                ruta_encontrada = ruta
                break
            else:
                resultado += f"❌ No existe: {ruta_absoluta}\n"
        
        if ruta_encontrada:
            try:
                conn = sqlite3.connect(ruta_encontrada)
                cursor = conn.cursor()
                
                # Listar tablas
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tablas = cursor.fetchall()
                
                resultado += f"\n📋 TABLAS ENCONTRADAS ({len(tablas)}):\n"
                for tabla in tablas:
                    resultado += f"   - {tabla[0]}\n"
                
                # Verificar tabla ventas
                if ('ventas',) in tablas:
                    resultado += f"\n✅ LA TABLA 'ventas' EXISTE\n"
                    
                    cursor.execute("SELECT COUNT(*) FROM ventas")
                    total = cursor.fetchone()[0]
                    resultado += f"📊 TOTAL DE REGISTROS: {total}\n"
                    
                    if total > 0:
                        cursor.execute("SELECT * FROM ventas LIMIT 3")
                        registros = cursor.fetchall()
                        resultado += f"\n📄 PRIMEROS 3 REGISTROS:\n"
                        for i, reg in enumerate(registros, 1):
                            resultado += f"   {i}. {reg}\n"
                else:
                    resultado += f"\n❌ LA TABLA 'ventas' NO EXISTE\n"
                
                conn.close()
                
            except sqlite3.Error as e:
                resultado += f"\n❌ ERROR AL CONECTAR: {e}\n"
        else:
            resultado += f"\n❌ NO SE ENCONTRÓ LA BASE DE DATOS\n"
        
        resultado += "\n" + "=" * 50 + "\n"
        resultado += "🏁 DIAGNÓSTICO COMPLETADO"
        
        text_diagnostico.insert(tk.END, resultado)
        text_diagnostico.config(state=tk.DISABLED)

    buttons_data = [
        ("👤 Nuevo Cliente", "#FF69B4", lambda: messagebox.showinfo("Función", "Función en desarrollo")),
        ("✏️ Editar Cliente", "#9370DB", lambda: messagebox.showinfo("Función", "Función en desarrollo")),
        ("📞 Contactar", "#20B2AA", lambda: messagebox.showinfo("Función", "Función en desarrollo")),
        ("📊 Ver Historial", "#FF6347", ver_historial_cliente),
        ("🔍 Diagnosticar DB", "#FF8C00", diagnosticar_base_datos),
        ("🔄 Actualizar", "#4169E1", lambda: cargar_datos())
    ]

    for i, (texto, color, comando) in enumerate(buttons_data):
        btn = tk.Button(buttons_container, text=texto, bg=color, fg="white",
                       font=("Segoe UI", 10, "bold"), padx=15, pady=8,
                       relief="flat", cursor="hand2", command=comando)
        btn.pack(side="left", padx=5)

        # Efectos hover
        def make_hover_effect(button, original_color):
            def on_enter(e):
                button.config(bg="#FF1493")
            def on_leave(e):
                button.config(bg=original_color)
            return on_enter, on_leave

        enter_effect, leave_effect = make_hover_effect(btn, color)
        btn.bind("<Enter>", enter_effect)
        btn.bind("<Leave>", leave_effect)

    # 🌟 Footer con información
    footer_frame = tk.Frame(ventana, bg="#FF1493", height=50)
    footer_frame.pack(fill="x")
    footer_frame.pack_propagate(False)

    footer_content = tk.Frame(footer_frame, bg="#FF1493")
    footer_content.pack(expand=True)

    tk.Label(footer_content, text="💎 Centro de Copiado & Papelería • 📞 +573215545788", 
             font=("Segoe UI", 10, "bold"), bg="#FF1493", fg="white").pack(pady=15)

    # 🎯 Eventos de teclado
    def keyboard_shortcuts(event):
        if event.state & 4:  # Ctrl presionado
            key = event.keysym.lower()
            if key == 'f':  # Ctrl+F para buscar
                search_entry.focus()
            elif key == 'r':  # Ctrl+R para actualizar
                cargar_datos()

    # Evento Enter en el campo de búsqueda
    search_entry.bind("<Return>", lambda e: buscar_cliente())

    ventana.bind("<KeyPress>", keyboard_shortcuts)
    ventana.focus_set()

    ventana.mainloop()

# Ejecutar si es llamado directamente
if __name__ == "__main__":
    iniciar_clientes()