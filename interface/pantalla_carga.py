import tkinter as tk
import pyttsx3
import math

def mostrar_carga(nombre="Eduardo"):
    # 🗣️ Voz de bienvenida (Keep as is, but ensure it doesn't cause issues if TTS isn't configured)
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
        engine.setProperty('volume', 1.0)
        mensaje = f"Bienvenido {nombre}, el sistema está listo"
        engine.say(mensaje)
        engine.runAndWait()
    except:
        pass  # Si hay problemas con el TTS, continúa sin sonido

    ventana = tk.Tk()
    ventana.title(f"VmPOS - Bienvenido {nombre} ✨")
    ventana.geometry("600x400")
    ventana.configure(bg="#ff9ff3") # Main background from menu_inicio.py
    ventana.resizable(False, False)
    
    # Centrar ventana
    ventana.update_idletasks()
    x = (ventana.winfo_screenwidth() // 2) - (600 // 2)
    y = (ventana.winfo_screenheight() // 2) - (400 // 2)
    ventana.geometry(f"600x400+{x}+{y}")

    # 🎨 Marco principal con nuevo color
    main_frame = tk.Frame(ventana, bg="#ffeaa7", width=560, height=360) # Light yellow from menu_inicio.py
    main_frame.place(relx=0.5, rely=0.5, anchor="center")
    main_frame.pack_propagate(False)

    # 📄 Header con iconos
    header_frame = tk.Frame(main_frame, bg="#e84393", height=80) # Dark pink from menu_inicio.py
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)

    # Iconos del header (ajustados a un tema más general/femenino si aplica)
    icons_frame = tk.Frame(header_frame, bg="#e84393")
    icons_frame.pack(expand=True)

    # Changed icons for a more feminine/welcoming feel
    icons = ["🌸", "✨", "🎀", "💖", "💫"]
    icon_labels = []
    
    for i, icon in enumerate(icons):
        label = tk.Label(icons_frame, text=icon, font=("Segoe UI Emoji", 18), 
                         bg="#e84393", fg="white")
        label.grid(row=0, column=i, padx=15, pady=20)
        icon_labels.append(label)

    # 🧠 Título principal
    tk.Label(main_frame, text=f"¡Hola {nombre}! 👋", 
             font=("Segoe UI", 24, "bold"), bg="#ffeaa7", fg="#e84393").pack(pady=(20, 5)) # Text color changed
    
    tk.Label(main_frame, text="Iniciando VmPOS...", 
             font=("Segoe UI", 16), bg="#ffeaa7", fg="#2d3436").pack(pady=(0, 30)) # Text color changed

    # 🔄 Marco del loader circular moderno
    loader_frame = tk.Frame(main_frame, bg="#ffeaa7", width=200, height=120)
    loader_frame.pack(pady=20)
    loader_frame.pack_propagate(False)

    # Canvas para loader circular
    canvas = tk.Canvas(loader_frame, width=120, height=120, bg="#ffeaa7", 
                       highlightthickness=0)
    canvas.place(relx=0.5, rely=0.5, anchor="center")

    # Crear círculos para el loader con colores de la paleta
    circles = []
    center_x, center_y = 60, 60
    radius = 35
    
    for i in range(12):
        angle = i * (360 / 12)
        x = center_x + radius * math.cos(math.radians(angle))
        y = center_y + radius * math.sin(math.radians(angle))
        
        circle = canvas.create_oval(x-4, y-4, x+4, y+4, 
                                     fill="#fbc531", outline="", width=0) # Changed initial circle color
        circles.append(circle)

    # 📊 Barra de progreso moderna
    progress_frame = tk.Frame(main_frame, bg="#ffeaa7")
    progress_frame.pack(pady=20, padx=60, fill="x")

    progress_bg = tk.Frame(progress_frame, bg="#fed3d7", height=6) # Lighter pink for progress bar background
    progress_bg.pack(fill="x")

    progress_bar = tk.Frame(progress_bg, bg="#fd79a8", height=6, width=0) # Rose pink for active bar
    progress_bar.pack(side="left")

    # 💬 Texto de estado
    status_label = tk.Label(main_frame, text="Preparando sistema...", 
                             font=("Segoe UI", 12), bg="#ffeaa7", fg="#2d3436") # Text color changed
    status_label.pack(pady=(10, 0))

    # 📱 Footer
    footer_frame = tk.Frame(main_frame, bg="#e84393", height=50) # Dark pink from menu_inicio.py
    footer_frame.pack(side="bottom", fill="x")
    footer_frame.pack_propagate(False)

    tk.Label(footer_frame, text="Centro de Copiado & Papelería", 
             font=("Segoe UI", 11, "bold"), bg="#e84393", fg="white").pack(pady=15)

    # ⚙️ Variables de animación
    progress_width = 0
    max_width = 480  # Ancho máximo de la barra
    
    status_messages = [
        "Preparando sistema... 🛠️",
        "Cargando módulos... 🧩",
        "Conectando base de datos... 🔗",
        "Verificando permisos... 🔑",
        "Inicializando interfaz... 🖥️",
        "Configurando impresoras... 🖨️",
        "Cargando productos... 🛍️",
        "Sistema listo... ✨"
    ]

    def animar_iconos(indice=0):
        # Animar iconos del header
        for i, label in enumerate(icon_labels):
            if i == indice % len(icon_labels):
                label.config(font=("Segoe UI Emoji", 22))
            else:
                label.config(font=("Segoe UI Emoji", 18))
        
        ventana.after(300, lambda: animar_iconos(indice + 1))

    # Reduced total cycles for faster loading (from 96 to 48)
    # Also reduced `after` delay from 80ms to 60ms for a snappier feel
    total_cycles = 48 
    
    def animar_loader(indice=0, ciclos=0):
        nonlocal progress_width
        
        if ciclos < total_cycles: 
            # Animar círculos con colores de la paleta
            for i, circle in enumerate(circles):
                if i == indice:
                    canvas.itemconfig(circle, fill="#fd79a8") # Rose pink
                elif i == (indice - 1) % 12:
                    canvas.itemconfig(circle, fill="#a29bfe") # Light purple
                elif i == (indice - 2) % 12:
                    canvas.itemconfig(circle, fill="#74b9ff") # Light blue
                else:
                    canvas.itemconfig(circle, fill="#fed3d7") # Lighter pink background
            
            # Animar barra de progreso
            progress_width = min(max_width, (ciclos / (total_cycles - 1)) * max_width) # Adjusted division for final fill
            progress_bar.config(width=int(progress_width))
            
            # Cambiar mensaje de estado (adjusted division for new cycle count)
            if ciclos % (total_cycles // len(status_messages)) == 0 and ciclos // (total_cycles // len(status_messages)) < len(status_messages):
                status_label.config(text=status_messages[ciclos // (total_cycles // len(status_messages))])
            
            ventana.update()
            ventana.after(60, lambda: animar_loader((indice + 1) % 12, ciclos + 1)) # Reduced delay
        else:
            # Finalizar animación
            status_label.config(text="¡Listo! Abriendo sistema... 🚀")
            progress_bar.config(width=max_width, bg="#55efc4") # Teal for completion
            ventana.update()
            ventana.after(300, ventana.destroy) # Slightly faster destroy after completion

    # Iniciar animaciones
    ventana.after(200, animar_iconos)
    ventana.after(200, animar_loader) # Start loader slightly faster
    
    ventana.mainloop()

if __name__ == "__main__":
    mostrar_carga("Sofía") # Example name