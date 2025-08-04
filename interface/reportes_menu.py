import tkinter as tk
from tkinter import ttk

def abrir_reporte(tipo):
    print(f"Abrir reporte: {tipo}")  # Aquí puedes conectar cada tipo a su función

def crear_cuadro(padre, texto, color, tipo, icon): # Added icon parameter
    frame = tk.Frame(padre, width=280, height=120, bg="white", bd=2, relief="solid") # Changed background to white, added border
    frame.pack_propagate(False)
    frame.grid_propagate(False)

    # Header for the card (similar to stats cards in menu_inicio)
    card_header = tk.Frame(frame, bg=color, height=10) # Thicker header
    card_header.pack(fill="x")

    # Content of the card
    card_content = tk.Frame(frame, bg="white")
    card_content.pack(fill="both", expand=True, padx=10, pady=5) # Reduced padding

    tk.Label(card_content, text=icon, font=("Segoe UI Emoji", 28), bg="white", fg=color).pack(pady=5) # Icon with color
    tk.Label(card_content, text=texto, font=("Segoe UI", 12, "bold"), bg="white", fg="#2d3436").pack() # Darker text color

    # Hover effects for the frame and its children
    def on_enter(e):
        frame.config(relief="raised", bd=3) # Pop out effect
    def on_leave(e):
        frame.config(relief="solid", bd=2) # Back to normal

    # Press effect: When button is clicked down
    def on_press(e):
        frame.config(relief="sunken", bd=3) # Sunken effect when pressed

    # Release effect: When button is released after clicking
    def on_release(e):
        # Only change back if the mouse is still within the button area
        if frame.winfo_containing(e.x_root, e.y_root) == frame:
            frame.config(relief="raised", bd=3) # Back to raised if still hovered
        else:
            frame.config(relief="solid", bd=2) # Back to solid if mouse left

        abrir_reporte(tipo) # Call the report function on release


    frame.bind("<Enter>", on_enter)
    frame.bind("<Leave>", on_leave)
    frame.bind("<ButtonPress-1>", on_press)    # Bind for mouse click down
    frame.bind("<ButtonRelease-1>", on_release) # Bind for mouse click release

    # Apply bindings to all children widgets so clicks anywhere on the card work
    card_header.bind("<Enter>", on_enter)
    card_header.bind("<Leave>", on_leave)
    card_header.bind("<ButtonPress-1>", on_press)
    card_header.bind("<ButtonRelease-1>", on_release)

    card_content.bind("<Enter>", on_enter)
    card_content.bind("<Leave>", on_leave)
    card_content.bind("<ButtonPress-1>", on_press)
    card_content.bind("<ButtonRelease-1>", on_release)

    for widget in card_content.winfo_children():
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
        widget.bind("<ButtonPress-1>", on_press)
        widget.bind("<ButtonRelease-1>", on_release)


    return frame

def iniciar_reportes():
    ventana = tk.Tk()
    ventana.title("REPORTES - VmPOS")
    ventana.geometry("980x540")
    ventana.resizable(False, False)
    ventana.configure(bg="#ff9ff3") # Main window background color from menu_inicio.py

    # Centrar ventana
    ventana.update_idletasks()
    x = (ventana.winfo_screenwidth() // 2) - (980 // 2)
    y = (ventana.winfo_screenheight() // 2) - (540 // 2)
    ventana.geometry(f"980x540+{x}+{y}")

    # 🎨 Header principal (Adapted from menu_inicio.py)
    header_frame = tk.Frame(ventana, bg="#e84393", height=80)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)

    header_left = tk.Frame(header_frame, bg="#e84393")
    header_left.pack(side="left", fill="y", padx=30)

    tk.Label(header_left, text="📊", font=("Segoe UI Emoji", 28), # New icon for reports
             bg="#e84393", fg="white").pack(side="left", pady=15)
    tk.Label(header_left, text="REPORTES", font=("Segoe UI", 24, "bold"),
             bg="#e84393", fg="white").pack(side="left", padx=(10, 0), pady=18)
    tk.Label(header_left, text="Análisis de Información", font=("Segoe UI", 12),
             bg="#e84393", fg="#ffd3e8").pack(side="left", padx=(15, 0), pady=20)

    # Add a right-aligned section for date/time if desired, similar to menu_inicio.py
    # For simplicity, keeping it minimal here.

    # 📊 Contenido principal (similar to main_content in menu_inicio.py)
    main_content = tk.Frame(ventana, bg="#ffeaa7")
    main_content.pack(fill="both", expand=True, padx=20, pady=20)

    tk.Label(main_content, text="✨ SELECCIONE UN REPORTE", font=("Segoe UI", 16, "bold"),
             bg="#ffeaa7", fg="#e84393").pack(pady=20)

    panel = tk.Frame(main_content, bg="#ffeaa7") # Changed panel background
    panel.pack(expand=True) # Allow panel to expand

    # 📦 Configuración de reportes en cuadrícula 2x3 con iconos y colores de menu_inicio.py
    opciones = [
        ("Reportes Diarios", "#fd79a8", "diario", "☀️"), # Rose pink, sun icon
        ("Reportes Semanales", "#74b9ff", "semanal", "🗓️"), # Light blue, calendar icon
        ("Reportes Mensuales", "#a29bfe", "mensual", "🌙"), # Light purple, moon icon
        ("Ganancia por Mes", "#55efc4", "graf_ganancia", "💰"), # Teal, money bag icon
        ("Ventas por Mes", "#ff7675", "graf_ventas", "📈"), # Coral, chart icon
        ("Productos Más Vendidos", "#fdcb6e", "graf_categoria", "⭐"), # Orange-yellow, star icon
    ]

    for i in range(2):  # Filas
        fila = tk.Frame(panel, bg="#ffeaa7") # Changed fila background
        fila.pack(pady=10)
        for j in range(3):  # Columnas
            index = i * 3 + j
            if index < len(opciones):
                texto, color, tipo, icon = opciones[index]
                cuadro = crear_cuadro(fila, texto, color, tipo, icon)
                cuadro.pack(side="left", padx=15)

    # 📊 Footer con información del sistema (Copied from menu_inicio.py)
    footer = tk.Frame(ventana, bg="#e84393", height=50)
    footer.pack(fill="x", side="bottom") # Ensure footer is at the bottom
    footer.pack_propagate(False)

    footer_left = tk.Frame(footer, bg="#e84393")
    footer_left.pack(side="left", padx=20, pady=10)

    footer_right = tk.Frame(footer, bg="#e84393")
    footer_right.pack(side="right", padx=20, pady=10)

    tk.Label(footer_left, text="📍 Puerto Colombia • 📞 +573215545788",
             font=("Segoe UI", 10), bg="#e84393", fg="white").pack()

    tk.Label(footer_right, text="✨ VmPOS v3.1.0 • Sistema Activo 💖",
             font=("Segoe UI", 10), bg="#e84393", fg="#ffd3e8").pack()

    ventana.mainloop()

if __name__ == "__main__":
    iniciar_reportes()