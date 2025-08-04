import tkinter as tk
from tkinter import messagebox
import os
import shutil
from datetime import datetime

def abrir_config(tipo):
    """
    Handles the opening of different configuration functionalities based on 'tipo'.
    """
    if tipo == "restaurar_db":
        restaurar_base_datos()
    elif tipo == "backup_db":
        crear_backup()
    elif tipo == "limpiar_logs":
        limpiar_logs()
    elif tipo == "actualizar_sistema":
        actualizar_sistema()
    elif tipo == "configurar_impresora":
        configurar_impresora()
    elif tipo == "exportar_datos":
        exportar_datos()

def restaurar_base_datos():
    """
    Prompts the user to confirm database restoration and simulates the process.
    """
    respuesta = messagebox.askyesno(
        "💖 Restaurar Base de Datos",
        "¿Estás segura de que deseas restaurar la base de datos?\n\n"
        "⚠️ Esta acción eliminará todos los datos actuales.\n"
        "✨ Se recomienda hacer un backup primero."
    )
    if respuesta:
        try:
            # Here would be the actual database restoration logic
            # For demonstration, we just show a success message
            messagebox.showinfo("✅ Éxito", "¡Base de datos restaurada exitosamente! 💎")
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudo restaurar la base de datos:\n{e}")

def crear_backup():
    """
    Simulates creating a backup of the system data.
    """
    try:
        fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_backup = f"backup_vmpos_{fecha}.db"
        
        # In a real application, you would copy or dump your database here.
        # Example (conceptual): shutil.copyfile("path/to/your/database.db", f"./backups/{nombre_backup}")
        
        # Ensure a 'backups' directory exists if you plan to save files
        # os.makedirs("./backups", exist_ok=True) 

        messagebox.showinfo("✅ Backup Creado", 
                            f"🌸 ¡Backup creado exitosamente!\n\n"
                            f"📁 Archivo: {nombre_backup}\n"
                            f"📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
                            f"💾 Ubicación: ./backups/ (simulado)") # Added simulated to clarify
    except Exception as e:
        messagebox.showerror("❌ Error", f"No se pudo crear el backup:\n{e}")

def limpiar_logs():
    """
    Prompts the user to confirm log file cleanup and simulates the process.
    """
    respuesta = messagebox.askyesno(
        "🧹 Limpiar Logs",
        "¿Deseas limpiar todos los archivos de log?\n\n"
        "💡 Esto ayudará a liberar espacio en disco."
    )
    if respuesta:
        # Here would be the actual log cleaning logic, e.g.,
        # for filename in os.listdir('./logs'):
        #     if filename.endswith('.log'):
        #         os.remove(os.path.join('./logs', filename))
        messagebox.showinfo("✅ Limpieza Completa", "¡Logs eliminados exitosamente! ✨")

def actualizar_sistema():
    """
    Simulates checking for and applying system updates.
    """
    messagebox.showinfo("🚀 Actualizar Sistema", 
                        "🌟 Verificando actualizaciones...\n\n"
                        "✅ Tu sistema está actualizado\n"
                        "📅 Versión actual: VmPOS v3.1.0\n"
                        "💖 ¡Todo funciona perfectamente!")

def configurar_impresora():
    """
    Simulates opening printer configuration settings.
    """
    messagebox.showinfo("🖨️ Configurar Impresora", 
                        "⚙️ Abriendo configuración de impresora...\n\n"
                        "💡 Asegúrate de que la impresora esté conectada\n"
                        "🔌 Puerto USB recomendado\n"
                        "📄 Papel térmico 58mm o 80mm")

def exportar_datos():
    """
    Simulates the process of exporting data.
    """
    messagebox.showinfo("📊 Exportar Datos", 
                        "📋 Preparando exportación...\n\n"
                        "✅ Productos: Listo\n"
                        "✅ Ventas: Listo\n"
                        "✅ Clientes: Listo\n"
                        "💾 Guardando en formato Excel...")

def crear_cuadro(padre, texto, icono, color, tipo):
    """
    Creates a styled interactive square button for configuration options.
    """
    frame = tk.Frame(padre, width=320, height=160, bg=color, relief="raised", bd=3, cursor="hand2")
    frame.pack_propagate(False)

    # Internal container to center content
    content_frame = tk.Frame(frame, bg=color)
    content_frame.pack(expand=True, fill="both")

    # Large icon
    icon_label = tk.Label(content_frame, text=icono, font=("Segoe UI Emoji", 36), 
                          bg=color, fg="white")
    icon_label.pack(pady=(20, 10))

    # Main text
    text_label = tk.Label(content_frame, text=texto, font=("Segoe UI", 12, "bold"), 
                          bg=color, fg="white", wraplength=280, justify="center")
    text_label.pack(pady=(0, 20))

    # Hover effects
    def on_enter(e):
        frame.config(bg="#FF1493", relief="raised", bd=4)
        content_frame.config(bg="#FF1493")
        icon_label.config(bg="#FF1493")
        text_label.config(bg="#FF1493")

    def on_leave(e):
        frame.config(bg=color, relief="raised", bd=3)
        content_frame.config(bg=color)
        icon_label.config(bg=color)
        text_label.config(bg=color)

    def on_click(e):
        # Click effect
        frame.config(relief="sunken", bd=2)
        frame.after(100, lambda: frame.config(relief="raised", bd=3))
        abrir_config(tipo)

    # Bind events to all elements within the square
    for widget in [frame, content_frame, icon_label, text_label]:
        widget.bind("<Button-1>", on_click)
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    return frame

def iniciar_configuracion():
    """
    Initializes and displays the main configuration window.
    """
    ventana = tk.Tk()
    ventana.title("⚙️ Configuración - VmPOS")
    ventana.geometry("1100x700")
    ventana.configure(bg="#FFE4F1")
    ventana.resizable(False, False)
    
    # Center window
    ventana.update_idletasks()
    x = (ventana.winfo_screenwidth() // 2) - (550)
    y = (ventana.winfo_screenheight() // 2) - (350)
    ventana.geometry(f"1100x700+{x}+{y}")

    # 🌸 Header principal con gradiente
    header_frame = tk.Frame(ventana, bg="#FF1493", height=100)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)

    # Header content
    header_content = tk.Frame(header_frame, bg="#FF1493")
    header_content.pack(expand=True, fill="both")

    title_container = tk.Frame(header_content, bg="#FF1493")
    title_container.pack(expand=True)

    tk.Label(title_container, text="⚙️", font=("Segoe UI Emoji", 40), 
             bg="#FF1493", fg="white").pack(side="left", pady=25, padx=(50, 15))
    tk.Label(title_container, text="CONFIGURACIÓN DEL SISTEMA", font=("Segoe UI", 22, "bold"), 
             bg="#FF1493", fg="white").pack(side="left", pady=30)
    tk.Label(title_container, text="✨", font=("Segoe UI Emoji", 40), 
             bg="#FF1493", fg="white").pack(side="left", pady=25, padx=(15, 50))

    # 💖 Subtitle
    subtitle_frame = tk.Frame(ventana, bg="#FFDDEE", height=60)
    subtitle_frame.pack(fill="x")
    subtitle_frame.pack_propagate(False)

    tk.Label(subtitle_frame, text="🌸 Personaliza y mantén tu sistema siempre actualizado 🌸", 
             font=("Segoe UI", 14), bg="#FFDDEE", fg="#C71585").pack(expand=True)

    # 🎀 Main configuration panel
    main_panel = tk.Frame(ventana, bg="#FFE4F1")
    main_panel.pack(fill="both", expand=True, pady=30, padx=40)

    # 📊 System information panel
    info_frame = tk.Frame(main_panel, bg="#FFC0CB", relief="raised", bd=2, height=100)
    info_frame.pack(fill="x", pady=(0, 30))
    info_frame.pack_propagate(False)

    info_content = tk.Frame(info_frame, bg="#FFC0CB")
    info_content.pack(expand=True, fill="both", padx=30, pady=20)

    # System information in columns
    col1 = tk.Frame(info_content, bg="#FFC0CB")
    col1.pack(side="left", fill="both", expand=True)

    col2 = tk.Frame(info_content, bg="#FFC0CB")
    col2.pack(side="left", fill="both", expand=True)

    col3 = tk.Frame(info_content, bg="#FFC0CB")
    col3.pack(side="left", fill="both", expand=True)

    # System information labels
    tk.Label(col1, text="💻 Sistema", font=("Segoe UI", 10, "bold"), 
             bg="#FFC0CB", fg="#8B0054").pack()
    tk.Label(col1, text="VmPOS v3.1.0", font=("Segoe UI", 12), 
             bg="#FFC0CB", fg="#FF1493").pack()

    tk.Label(col2, text="📅 Última Actualización", font=("Segoe UI", 10, "bold"), 
             bg="#FFC0CB", fg="#8B0054").pack()
    tk.Label(col2, text="01/08/2025", font=("Segoe UI", 12), 
             bg="#FFC0CB", fg="#FF1493").pack()

    tk.Label(col3, text="💾 Base de Datos", font=("Segoe UI", 10, "bold"), 
             bg="#FFC0CB", fg="#8B0054").pack()
    tk.Label(col3, text="Conectada ✅", font=("Segoe UI", 12), 
             bg="#FFC0CB", fg="#32CD32").pack()

    # 🎨 Configuration options panel in a grid-like fashion
    options_container = tk.Frame(main_panel, bg="#FFE4F1")
    options_container.pack(fill="both", expand=True)

    # Options organized in rows
    opciones = [
        # First row
        [
            ("🔄 Restaurar\nBase de Datos", "🔄", "#FF6B6B", "restaurar_db"),
            ("💾 Crear Copia\nde Seguridad", "💾", "#4ECDC4", "backup_db"),
            ("🧹 Limpiar\nArchivos Log", "🧹", "#45B7D1", "limpiar_logs")
        ],
        # Second row
        [
            ("🚀 Actualizar\nSistema", "🚀", "#96CEB4", "actualizar_sistema"),
            ("🖨️ Configurar\nImpresora", "🖨️", "#FECA57", "configurar_impresora"),
            ("📊 Exportar\nDatos", "📊", "#FF9FF3", "exportar_datos")
        ]
    ]

    for fila_opciones in opciones:
        fila_frame = tk.Frame(options_container, bg="#FFE4F1")
        fila_frame.pack(pady=20)
        
        for texto, icono, color, tipo in fila_opciones:
            cuadro = crear_cuadro(fila_frame, texto, icono, color, tipo)
            cuadro.pack(side="left", padx=25)

    # 🌟 Quick actions panel
    quick_actions_frame = tk.Frame(ventana, bg="#FF1493", height=80)
    quick_actions_frame.pack(fill="x")
    quick_actions_frame.pack_propagate(False)

    quick_content = tk.Frame(quick_actions_frame, bg="#FF1493")
    quick_content.pack(expand=True, fill="both")

    tk.Label(quick_content, text="⚡ ACCIONES RÁPIDAS", font=("Segoe UI", 12, "bold"), 
             bg="#FF1493", fg="white").pack(side="left", padx=30, pady=25)

    # Quick access buttons
    quick_buttons = [
        ("🔧 Diagnóstico", lambda: messagebox.showinfo("🔧", "Sistema funcionando correctamente ✅")),
        ("📋 Logs del Sistema", lambda: messagebox.showinfo("📋", "Mostrando logs recientes...")),
        ("🌐 Verificar Conexión", lambda: messagebox.showinfo("🌐", "Conexión a internet: OK ✅")),
        ("🎨 Cambiar Tema", lambda: messagebox.showinfo("🎨", "Tema femenino activo 💖"))
    ]

    quick_buttons_frame = tk.Frame(quick_content, bg="#FF1493")
    quick_buttons_frame.pack(side="right", padx=30, pady=15)

    for texto, comando in quick_buttons:
        btn = tk.Button(quick_buttons_frame, text=texto, command=comando,
                        bg="#FFDDEE", fg="#C71585", font=("Segoe UI", 9, "bold"),
                        relief="flat", padx=12, pady=8, cursor="hand2")
        btn.pack(side="left", padx=5)

        # Hover effects for quick buttons
        def make_quick_hover(button):
            def on_enter(e):
                button.config(bg="#FF69B4", fg="white")
            def on_leave(e):
                button.config(bg="#FFDDEE", fg="#C71585")
            return on_enter, on_leave

        enter_fx, leave_fx = make_quick_hover(btn)
        btn.bind("<Enter>", enter_fx)
        btn.bind("<Leave>", leave_fx)

    # 🎯 Keyboard events
    def keyboard_shortcuts(event):
        if event.state & 4:   # Ctrl pressed
            key = event.keysym.lower()
            if key == 'b':    # Ctrl+B for backup
                crear_backup()
            elif key == 'r':  # Ctrl+R for restore
                restaurar_base_datos() # Corrected function call

    ventana.bind("<Key>", keyboard_shortcuts)

    ventana.mainloop()

if __name__ == "__main__":
    iniciar_configuracion()