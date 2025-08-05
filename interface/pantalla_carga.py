#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pantalla de carga optimizada para Sistema VM
Archivo: interface/pantalla_carga.py
"""

import tkinter as tk
import math
import threading

def mostrar_carga(nombre="Usuario", usuario_info=None):
    """
    Muestra una pantalla de carga optimizada (más rápida)
    Args:
        nombre (str): Nombre del usuario (se usará como fallback si no hay usuario_info)
        usuario_info (dict): Información completa del usuario (con claves 'usuario' y 'permisos')
    """
    
    def reproducir_bienvenida():
        """Reproduce mensaje de bienvenida en hilo separado (opcional)"""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty('rate', 170)  # Más rápido
            engine.setProperty('volume', 0.8)  # Volumen más bajo
            mensaje = f"Bienvenido {nombre}, sistema listo"
            engine.say(mensaje)
            engine.runAndWait()
        except:
            pass  # Si hay problemas con TTS, continúa sin sonido

    # Iniciar TTS en hilo separado para no bloquear la UI
    threading.Thread(target=reproducir_bienvenida, daemon=True).start()

    ventana = tk.Tk()
    ventana.title(f"VmPOS - Bienvenido {nombre} ✨")
    ventana.geometry("550x350")  # Tamaño reducido
    ventana.configure(bg="#ff9ff3")
    ventana.resizable(False, False)
    ventana.overrideredirect(True)  # Sin barra de título para carga más elegante
    
    # Centrar ventana
    ventana.update_idletasks()
    x = (ventana.winfo_screenwidth() // 2) - (550 // 2)
    y = (ventana.winfo_screenheight() // 2) - (350 // 2)
    ventana.geometry(f"550x350+{x}+{y}")

    # Marco principal con borde redondeado simulado
    main_frame = tk.Frame(ventana, bg="#ffeaa7", width=530, height=330)
    main_frame.place(relx=0.5, rely=0.5, anchor="center")
    main_frame.pack_propagate(False)

    # Header compacto
    header_frame = tk.Frame(main_frame, bg="#e84393", height=60)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)

    # Iconos animados del header (reducidos)
    icons_frame = tk.Frame(header_frame, bg="#e84393")
    icons_frame.pack(expand=True)

    icons = ["🌸", "💖", "✨"]  # Menos iconos para mayor velocidad
    icon_labels = []
    
    for i, icon in enumerate(icons):
        label = tk.Label(icons_frame, text=icon, font=("Segoe UI Emoji", 16), 
                         bg="#e84393", fg="white")
        label.grid(row=0, column=i, padx=20, pady=15)
        icon_labels.append(label)

    # Información del usuario
    user_info_frame = tk.Frame(main_frame, bg="#ffeaa7")
    user_info_frame.pack(pady=15)

    if usuario_info:
        # Corrección: se usan las claves correctas 'usuario' y 'permisos'
        nombre_usuario = usuario_info.get('usuario', 'Usuario')
        permisos_usuario = usuario_info.get('permisos', 'No definido')

        tk.Label(user_info_frame, text=f"¡Hola {nombre_usuario.capitalize()}! �", 
                 font=("Segoe UI", 20, "bold"), bg="#ffeaa7", fg="#e84393").pack()
        
        tk.Label(user_info_frame, text=f"Rol: {permisos_usuario.capitalize()}", 
                 font=("Segoe UI", 12), bg="#ffeaa7", fg="#2d3436").pack()
        
        tk.Label(user_info_frame, text="Iniciando VmPOS...", 
                 font=("Segoe UI", 14), bg="#ffeaa7", fg="#636e72").pack(pady=(5, 0))
    else:
        tk.Label(user_info_frame, text=f"¡Hola {nombre}! 👋", 
                 font=("Segoe UI", 20, "bold"), bg="#ffeaa7", fg="#e84393").pack()
        
        tk.Label(user_info_frame, text="Iniciando VmPOS...", 
                 font=("Segoe UI", 14), bg="#ffeaa7", fg="#636e72").pack(pady=(10, 0))

    # Loader circular más pequeño y rápido
    loader_frame = tk.Frame(main_frame, bg="#ffeaa7", width=100, height=100)
    loader_frame.pack(pady=15)
    loader_frame.pack_propagate(False)

    canvas = tk.Canvas(loader_frame, width=80, height=80, bg="#ffeaa7", 
                       highlightthickness=0)
    canvas.place(relx=0.5, rely=0.5, anchor="center")

    # Círculos del loader (menos para mejor rendimiento)
    circles = []
    center_x, center_y = 40, 40
    radius = 25
    
    for i in range(8):  # Reducido de 12 a 8
        angle = i * (360 / 8)
        x = center_x + radius * math.cos(math.radians(angle))
        y = center_y + radius * math.sin(math.radians(angle))
        
        circle = canvas.create_oval(x-3, y-3, x+3, y+3, 
                                     fill="#fed3d7", outline="", width=0)
        circles.append(circle)

    # Barra de progreso más pequeña
    progress_frame = tk.Frame(main_frame, bg="#ffeaa7")
    progress_frame.pack(pady=10, padx=40, fill="x")

    progress_bg = tk.Frame(progress_frame, bg="#fed3d7", height=4)
    progress_bg.pack(fill="x")

    progress_bar = tk.Frame(progress_bg, bg="#fd79a8", height=4, width=0)
    progress_bar.pack(side="left")

    # Estado de carga
    status_label = tk.Label(main_frame, text="Preparando...", 
                            font=("Segoe UI", 11), bg="#ffeaa7", fg="#2d3436")
    status_label.pack(pady=5)

    # Footer compacto
    footer_frame = tk.Frame(main_frame, bg="#e84393", height=40)
    footer_frame.pack(side="bottom", fill="x")
    footer_frame.pack_propagate(False)

    tk.Label(footer_frame, text="VmPOS • Centro de Copiado & Papelería", 
             font=("Segoe UI", 10, "bold"), bg="#e84393", fg="white").pack(pady=10)

    # Variables de animación (optimizadas)
    progress_width = 0
    max_width = 470  # Ancho máximo ajustado
    
    # Mensajes de estado reducidos
    status_messages = [
        "Iniciando... 🚀",
        "Cargando datos... 📊", 
        "Preparando interfaz... 🖥️",
        "Sistema listo... ✨"
    ]

    def animar_iconos(indice=0):
        """Animación de iconos más rápida"""
        for i, label in enumerate(icon_labels):
            if i == indice % len(icon_labels):
                label.config(font=("Segoe UI Emoji", 20))
            else:
                label.config(font=("Segoe UI Emoji", 16))
        
        ventana.after(400, lambda: animar_iconos(indice + 1))

    # Animación mucho más rápida
    total_cycles = 20  # Reducido drásticamente de 48 a 20
    
    def animar_loader(indice=0, ciclos=0):
        nonlocal progress_width
        
        if ciclos < total_cycles:
            # Animar círculos del loader
            for i, circle in enumerate(circles):
                if i == indice:
                    canvas.itemconfig(circle, fill="#fd79a8")
                elif i == (indice - 1) % 8:
                    canvas.itemconfig(circle, fill="#a29bfe")
                else:
                    canvas.itemconfig(circle, fill="#fed3d7")
            
            # Animar barra de progreso
            progress_width = (ciclos / (total_cycles - 1)) * max_width
            progress_bar.config(width=int(progress_width))
            
            # Cambiar mensaje de estado
            message_index = min(ciclos // (total_cycles // len(status_messages)), len(status_messages) - 1)
            status_label.config(text=status_messages[message_index])
            
            ventana.update()
            ventana.after(50, lambda: animar_loader((indice + 1) % 8, ciclos + 1))  # Muy rápido
        else:
            # Finalizar
            status_label.config(text="¡Listo! 🎉")
            progress_bar.config(width=max_width, bg="#55efc4")
            ventana.update()
            ventana.after(200, ventana.destroy)  # Cerrar rápidamente

    # Iniciar animaciones
    ventana.after(100, animar_iconos)
    ventana.after(100, animar_loader)
    
    # Auto-cerrar por seguridad (por si algo falla)
    ventana.after(3000, ventana.destroy)
    
    ventana.mainloop()

# Función de prueba
if __name__ == "__main__":
    # Simular información de usuario
    usuario_test = {
        'usuario': 'Ana', # Cambiado a 'usuario'
        'permisos': 'Administrador' # Cambiado a 'permisos'
    }
    mostrar_carga("Ana", usuario_test)

