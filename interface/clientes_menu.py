import tkinter as tk
from tkinter import ttk
from datetime import datetime
import pandas as pd
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

    btn_search = tk.Button(search_frame, text="💖 Buscar", bg="#FF69B4", fg="white",
                          font=("Segoe UI", 10, "bold"), padx=15, pady=5,
                          relief="flat", cursor="hand2")
    btn_search.pack(side="left", padx=10, pady=10)

    btn_refresh = tk.Button(search_frame, text="🔄 Actualizar", bg="#9370DB", fg="white",
                           font=("Segoe UI", 10, "bold"), padx=15, pady=5,
                           relief="flat", cursor="hand2")
    btn_refresh.pack(side="left", padx=5, pady=10)

    # 📊 Panel de estadísticas rápidas
    stats_frame = tk.Frame(ventana, bg="#FFE4F1")
    stats_frame.pack(fill="x", pady=10, padx=10)

    stats_container = tk.Frame(stats_frame, bg="#FFE4F1")
    stats_container.pack()

    # Tarjetas de estadísticas
    stats_data = [
        ("👥", "Total Clientes", "127", "#FF69B4"),
        ("💎", "Clientes VIP", "23", "#9370DB"),
        ("🛍️", "Compras Hoy", "45", "#20B2AA"),
        ("💰", "Ventas del Mes", "$2,450,000", "#FF6347")
    ]

    for i, (icono, titulo, valor, color) in enumerate(stats_data):
        card = tk.Frame(stats_container, bg="white", relief="raised", bd=2, width=200, height=100)
        card.pack(side="left", padx=10, pady=5)
        card.pack_propagate(False)

        # Header colorido
        card_header = tk.Frame(card, bg=color, height=25)
        card_header.pack(fill="x")

        # Contenido
        card_content = tk.Frame(card, bg="white")
        card_content.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(card_content, text=icono, font=("Segoe UI Emoji", 20), bg="white").pack()
        tk.Label(card_content, text=titulo, font=("Segoe UI", 9, "bold"), 
                bg="white", fg="#666").pack()
        tk.Label(card_content, text=valor, font=("Segoe UI", 12, "bold"), 
                bg="white", fg=color).pack()

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

    # 📁 Cargar datos desde CSV
    def cargar_datos():
        tabla.delete(*tabla.get_children())
        ruta_csv = os.path.join(os.path.dirname(__file__), "..", "ventas.csv")
        if os.path.exists(ruta_csv):
            try:
                df = pd.read_csv(ruta_csv)
                for idx, row in df.iterrows():
                    # Alternar colores de filas
                    tag = "even" if idx % 2 == 0 else "odd"
                    tabla.insert("", "end", values=(
                        idx + 1,
                        row.get("Documento", "N/A"),
                        row.get("Cliente", "Cliente Anónimo"),
                        row.get("Fecha", "N/A"),
                        row.get("Hora", "N/A"),
                        f"${row.get('Total', 0):,.0f}" if pd.notna(row.get('Total')) else "$0"
                    ), tags=(tag,))
                
                # Configurar colores alternos
                tabla.tag_configure("even", background="#FFF0F5")
                tabla.tag_configure("odd", background="white")
                
            except Exception as e:
                tk.messagebox.showerror("Error", f"No se pudo cargar el archivo CSV: {e}")
        else:
            # Datos de ejemplo si no existe el archivo
            datos_ejemplo = [
                (1, "12345678", "María González", "01-08-2025", "14:30", "$125,000"),
                (2, "87654321", "Ana Rodríguez", "01-08-2025", "15:45", "$89,500"),
                (3, "11223344", "Carmen López", "31-07-2025", "16:20", "$67,800"),
                (4, "55667788", "Patricia Martín", "31-07-2025", "17:10", "$234,600"),
                (5, "99887766", "Elena Sánchez", "30-07-2025", "10:15", "$156,900")
            ]
            
            for idx, datos in enumerate(datos_ejemplo):
                tag = "even" if idx % 2 == 0 else "odd"
                tabla.insert("", "end", values=datos, tags=(tag,))
            
            tabla.tag_configure("even", background="#FFF0F5")
            tabla.tag_configure("odd", background="white")

    cargar_datos()

    # 💝 Panel de acciones con botones femeninos
    actions_frame = tk.Frame(ventana, bg="#FFE4F1")
    actions_frame.pack(fill="x", pady=10, padx=10)

    buttons_container = tk.Frame(actions_frame, bg="#FFE4F1")
    buttons_container.pack()

    buttons_data = [
        ("👤 Nuevo Cliente", "#FF69B4", lambda: print("Nuevo cliente")),
        ("✏️ Editar Cliente", "#9370DB", lambda: print("Editar cliente")),
        ("📞 Contactar", "#20B2AA", lambda: print("Contactar cliente")),
        ("📊 Ver Historial", "#FF6347", lambda: print("Ver historial")),
        ("📋 Exportar Lista", "#32CD32", lambda: print("Exportar")),
        ("🗑️ Eliminar", "#DC143C", lambda: print("Eliminar"))
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

    ventana.bind("<KeyPress>", keyboard_shortcuts)
    ventana.focus_set()

    ventana.mainloop()

# Ejecutar si es llamado directamente
if __name__ == "__main__":
    iniciar_clientes()