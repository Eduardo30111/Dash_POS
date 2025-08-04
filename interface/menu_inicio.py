import tkinter as tk
from tkinter import ttk
import subprocess
from reportes_menu import iniciar_reportes
from clientes_menu import iniciar_clientes
from configuracion_menu import iniciar_configuracion
from gastos_menu import iniciar_gastos
from usuarios_menu import iniciar_usuarios
from pantalla_carga import mostrar_carga
import datetime

def iniciar_dashboard(usuario="Admin"):
    ventana = tk.Tk()
    ventana.title(f"VmPOS - Dashboard • {usuario}")
    ventana.geometry("1200x700")
    ventana.resizable(False, False)
    ventana.configure(bg="#ff9ff3")
    
    # Centrar ventana
    ventana.update_idletasks()
    x = (ventana.winfo_screenwidth() // 2) - (1200 // 2)
    y = (ventana.winfo_screenheight() // 2) - (700 // 2)
    ventana.geometry(f"1200x700+{x}+{y}")

    # 🎨 Header principal
    header_frame = tk.Frame(ventana, bg="#e84393", height=80)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)

    # Logo y título en header
    header_left = tk.Frame(header_frame, bg="#e84393")
    header_left.pack(side="left", fill="y", padx=30)
    
    tk.Label(header_left, text="🌸", font=("Segoe UI Emoji", 28), 
             bg="#e84393", fg="white").pack(side="left", pady=15)
    tk.Label(header_left, text="VmPOS", font=("Segoe UI", 24, "bold"), 
             bg="#e84393", fg="white").pack(side="left", padx=(10, 0), pady=18)
    tk.Label(header_left, text="Centro de Copiado & Papelería", font=("Segoe UI", 12), 
             bg="#e84393", fg="#ffd3e8").pack(side="left", padx=(15, 0), pady=20)

    # Info usuario en header
    header_right = tk.Frame(header_frame, bg="#e84393")
    header_right.pack(side="right", fill="y", padx=30)
    
    now = datetime.datetime.now()
    fecha_actual = now.strftime("%d/%m/%Y")
    hora_actual = now.strftime("%H:%M")
    
    tk.Label(header_right, text=f"👤 {usuario}", font=("Segoe UI", 14, "bold"), 
             bg="#e84393", fg="white").pack(anchor="e", pady=(12, 2))
    tk.Label(header_right, text=f"📅 {fecha_actual} • 🕐 {hora_actual}", font=("Segoe UI", 10), 
             bg="#e84393", fg="#ffd3e8").pack(anchor="e")
    tk.Label(header_right, text="👑 Administrador", font=("Segoe UI", 10), 
             bg="#e84393", fg="#ffd3e8").pack(anchor="e", pady=(2, 12))

    # 📊 Contenido principal
    main_content = tk.Frame(ventana, bg="#ffeaa7")
    main_content.pack(fill="both", expand=True, padx=20, pady=20)

    # 💰 Panel de estadísticas rápidas
    stats_frame = tk.Frame(main_content, bg="#ffeaa7")
    stats_frame.pack(fill="x", pady=(0, 20))

    stats = [
        ("💖", "Ventas Hoy", "$125,450", "#fd79a8"),
        ("🎀", "Productos", "1,247", "#74b9ff"),
        ("💎", "Clientes", "89", "#a29bfe"),
        ("🌈", "Pedidos", "23", "#55efc4")
    ]

    for i, (icono, titulo, valor, color) in enumerate(stats):
        stat_card = tk.Frame(stats_frame, bg="white", bd=2, relief="solid")
        stat_card.pack(side="left", fill="both", expand=True, padx=(0 if i == 0 else 10, 0))
        
        # Header colorido de la tarjeta
        card_header = tk.Frame(stat_card, bg=color, height=5)
        card_header.pack(fill="x")
        
        # Contenido de la tarjeta
        card_content = tk.Frame(stat_card, bg="white")
        card_content.pack(fill="both", expand=True, padx=20, pady=15)
        
        tk.Label(card_content, text=icono, font=("Segoe UI Emoji", 24), bg="white").pack()
        tk.Label(card_content, text=titulo, font=("Segoe UI", 11), bg="white", fg="#636e72").pack()
        tk.Label(card_content, text=valor, font=("Segoe UI", 16, "bold"), bg="white", fg="#2d3436").pack()

    # 🎛️ Panel principal de botones
    buttons_container = tk.Frame(main_content, bg="#ffeaa7")
    buttons_container.pack(fill="both", expand=True)

    # Panel izquierdo - Operaciones principales
    left_panel = tk.Frame(buttons_container, bg="white", bd=3, relief="solid")
    left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

    tk.Label(left_panel, text="✨ OPERACIONES PRINCIPALES", font=("Segoe UI", 14, "bold"), 
             bg="white", fg="#e84393").pack(pady=20)

    # Panel central - Gestión
    center_panel = tk.Frame(buttons_container, bg="white", bd=3, relief="solid")
    center_panel.pack(side="left", fill="both", expand=True, padx=5)

    tk.Label(center_panel, text="💫 GESTIÓN", font=("Segoe UI", 14, "bold"), 
             bg="white", fg="#e84393").pack(pady=20)

    # Panel derecho - Configuración
    right_panel = tk.Frame(buttons_container, bg="white", bd=3, relief="solid")
    right_panel.pack(side="right", fill="both", expand=True, padx=(10, 0))

    tk.Label(right_panel, text="🎨 CONFIGURACIÓN", font=("Segoe UI", 14, "bold"), 
             bg="white", fg="#e84393").pack(pady=20)

    def crear_boton_moderno(parent, texto, icono, color, comando):
        btn_frame = tk.Frame(parent, bg="white")
        btn_frame.pack(fill="x", padx=20, pady=8)
        
        btn = tk.Button(btn_frame, text=f"{icono}  {texto}", 
                       font=("Segoe UI", 12, "bold"), bg=color, fg="white",
                       bd=0, pady=15, cursor="hand2", command=comando,
                       relief="flat", anchor="w", padx=20)
        btn.pack(fill="x")
        
        # Efectos hover
        color_hover = {
            "#fd79a8": "#e84393",
            "#74b9ff": "#6c5ce7", 
            "#55efc4": "#00b894",
            "#ff7675": "#e17055",
            "#a29bfe": "#6c5ce7",
            "#fdcb6e": "#f39c12"
        }.get(color, "#e84393")
        
        def on_enter(e):
            btn.config(bg=color_hover)
        def on_leave(e):
            btn.config(bg=color)
            
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn

    def accion(nombre):
        if nombre == "Ventas":
            subprocess.Popen(["python", "ventas_menu.py"])
        elif nombre == "Inventario":
            subprocess.Popen(["python", "inventario_menu.py"])
        elif nombre == "Clientes":
            iniciar_clientes()
        elif nombre == "Reportes":
            iniciar_reportes()
        elif nombre == "Configuración":
            iniciar_configuracion()
        elif nombre == "Gastos":
            iniciar_gastos()
        elif nombre == "Usuarios":
            iniciar_usuarios()

    # Botones del panel izquierdo
    crear_boton_moderno(left_panel, "Nueva Venta", "💖", "#fd79a8", lambda: accion("Ventas"))
    crear_boton_moderno(left_panel, "Gestionar Inventario", "🎀", "#74b9ff", lambda: accion("Inventario"))
    crear_boton_moderno(left_panel, "Clientes", "💎", "#55efc4", lambda: accion("Clientes"))

    # Botones del panel central
    crear_boton_moderno(center_panel, "Reportes", "🌈", "#fdcb6e", lambda: accion("Reportes"))
    crear_boton_moderno(center_panel, "Control de Gastos", "🌸", "#ff7675", lambda: accion("Gastos"))

    # Botones del panel derecho
    crear_boton_moderno(right_panel, "Configuración", "✨", "#a29bfe", lambda: accion("Configuración"))
    crear_boton_moderno(right_panel, "Usuarios", "👸", "#fd79a8", lambda: accion("Usuarios"))

    # 📱 Panel de acceso rápido
    quick_access = tk.Frame(main_content, bg="#e84393", height=80)
    quick_access.pack(fill="x", pady=(20, 0))
    quick_access.pack_propagate(False)

    tk.Label(quick_access, text="💫 ACCESO RÁPIDO", font=("Segoe UI", 12, "bold"), 
             bg="#e84393", fg="white").pack(side="left", padx=20, pady=25)

    # Botones de acceso rápido
    quick_buttons = [
        ("🌟", "Nueva Factura", "#fd79a8"),
        ("💎", "Consultar Stock", "#74b9ff"),
        ("🎀", "Backup", "#55efc4"),
        ("✨", "Sincronizar", "#fdcb6e")
    ]

    quick_frame = tk.Frame(quick_access, bg="#e84393")
    quick_frame.pack(side="right", padx=20, pady=15)

    for icono, texto, color in quick_buttons:
        quick_btn = tk.Button(quick_frame, text=f"{icono}\n{texto}", 
                             font=("Segoe UI", 9, "bold"), bg=color, fg="white",
                             bd=0, cursor="hand2", relief="flat", width=10, height=2)
        quick_btn.pack(side="left", padx=5)

    # 📊 Footer con información del sistema
    footer = tk.Frame(ventana, bg="#e84393", height=50)
    footer.pack(fill="x")
    footer.pack_propagate(False)

    footer_left = tk.Frame(footer, bg="#e84393")
    footer_left.pack(side="left", padx=20, pady=10)

    footer_right = tk.Frame(footer, bg="#e84393")
    footer_right.pack(side="right", padx=20, pady=10)

    tk.Label(footer_left, text="📍 Puerto Colombia • 📞 +573215545788", 
             font=("Segoe UI", 10), bg="#e84393", fg="white").pack()

    tk.Label(footer_right, text="✨ VmPOS v3.1.0 • Sistema Activo 💖", 
             font=("Segoe UI", 10), bg="#e84393", fg="#ffd3e8").pack()

    # 🎯 Eventos de teclado
    def shortcuts(event):
        key = event.keysym.lower()
        if event.state & 4:  # Ctrl presionado
            if key == 'v':
                accion("Ventas")
            elif key == 'i':
                accion("Inventario")
            elif key == 'c':
                accion("Clientes")
            elif key == 'r':
                accion("Reportes")

    ventana.bind("<KeyPress>", shortcuts)
    ventana.focus_set()

    ventana.mainloop()

# 🚀 Activador principal del sistema
if __name__ == "__main__":
    mostrar_carga(nombre="Admin")
    iniciar_dashboard(usuario="Admin")