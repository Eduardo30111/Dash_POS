#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Archivo: iniciar_sesion.py
Interfaz de inicio de sesión principal para VmPOS.
Actualizado para usar la base de datos de usuarios.
"""

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
# Importar los módulos necesarios. Es crucial que no estén comentados.
import menu_inicio
from pantalla_carga import mostrar_carga

# Importar funciones de la base de datos de usuarios
from usuarios_db import (
    obtener_usuario_por_credenciales, 
    crear_tablas_iniciales,
    inicializar_admin_default
)

# --- Variables necesarias (telefono es estático) ---
telefono = "+573215545788"

def inicializar_sistema():
    """Inicializa el sistema de base de datos de usuarios al arrancar."""
    try:
        print("🔧 Inicializando sistema de autenticación...")
        crear_tablas_iniciales()
        inicializar_admin_default()
        print("✅ Sistema de autenticación listo.")
    except Exception as e:
        print(f"❌ Error al inicializar sistema: {e}")

# 🚨 Sistema de alertas personalizadas
def mostrar_alerta_bonita(titulo, mensaje, tipo="error"):
    """
    Muestra una ventana de alerta personalizada con un estilo moderno.
    """
    alerta = tk.Toplevel()
    alerta.title("💫 Notificación")
    alerta.geometry("400x280")
    alerta.configure(bg="#FCE4EC") # Rosa muy claro de fondo de alerta
    alerta.resizable(False, False)
    alerta.grab_set()    # Hacer modal
    
    # Centrar alerta
    alerta.update_idletasks()
    x = (alerta.winfo_screenwidth() // 2) - (400 // 2)
    y = (alerta.winfo_screenheight() // 2) - (280 // 2)
    alerta.geometry(f"400x280+{x}+{y}")
    
    # Colores según tipo
    if tipo == "error":
        color_header = "#FF8A80" # Rojo/rosa suave para error
        icono = "⚠️"
        color_boton = "#F44336"
    elif tipo == "warning":
        color_header = "#FFD180" # Naranja/amarillo suave para advertencia
        icono = "💡"
        color_boton = "#FFAB40"
    else: # success
        color_header = "#A7FFEB" # Verde/azul suave para éxito
        icono = "✅"
        color_boton = "#69F0AE"
    
    # Marco principal
    main_frame = tk.Frame(alerta, bg="white", bd=2, relief="solid")
    main_frame.pack(fill="both", expand=True, padx=15, pady=15)
    
    # Header colorido
    header_frame = tk.Frame(main_frame, bg=color_header, height=80)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)
    
    tk.Label(header_frame, text=icono, font=("Segoe UI Emoji", 32), 
             bg=color_header, fg="white").pack(pady=(15, 5))
    tk.Label(header_frame, text=titulo, font=("Segoe UI", 14, "bold"), 
             bg=color_header, fg="white").pack()
    
    # Contenido del mensaje
    content_frame = tk.Frame(main_frame, bg="white")
    content_frame.pack(expand=True, fill="both", padx=30, pady=30)
    
    tk.Label(content_frame, text=mensaje, font=("Segoe UI", 12), 
             bg="white", fg="#2d3436", wraplength=300, justify="center").pack(expand=True)
    
    # Botón de cerrar
    def cerrar_alerta():
        alerta.destroy()
    
    btn_cerrar = tk.Button(content_frame, text="💖 Entendido", 
                             font=("Segoe UI", 11, "bold"), bg=color_boton, fg="white",
                             bd=0, pady=8, cursor="hand2", command=cerrar_alerta,
                             relief="flat", width=20)
    btn_cerrar.pack(pady=(10, 0))
    
    # Efectos hover
    def on_enter(e):
        btn_cerrar.config(bg="#9E9E9E") # Gris suave para hover
    def on_leave(e):
        btn_cerrar.config(bg=color_boton)
    
    btn_cerrar.bind("<Enter>", on_enter)
    btn_cerrar.bind("<Leave>", on_leave)
    
    # Auto-cerrar después de 3 segundos
    alerta.after(3000, cerrar_alerta)
    
    # Focus y tecla Enter
    btn_cerrar.focus()
    alerta.bind("<Return>", lambda e: cerrar_alerta())

def validar_campos():
    """
    Realiza la validación de campos y autenticación usando la base de datos.
    Retorna una tupla (bool, dict) donde el booleano indica si la validación
    fue exitosa y el diccionario contiene los datos del usuario si lo fue.
    """
    usuario = usuario_var.get().strip()
    clave = pass_var.get().strip()
    
    # Limpiar estilos previos
    user_frame.config(bg="#F3E5F5", bd=2) # Morado muy claro
    pass_frame.config(bg="#F3E5F5", bd=2) # Morado muy claro
    
    if not usuario:
        user_frame.config(bg="#FFCDD2", bd=3) # Rosa más fuerte para error
        mostrar_alerta_bonita(
            "¡Ups! Campo vacío 😊",
            "Por favor, ingresa tu nombre de usuario.\n\n¡No te olvides de este importante detalle!",
            "warning"
        )
        entry_user.focus()
        return False, None
    
    if not clave:
        pass_frame.config(bg="#FFCDD2", bd=3) # Rosa más fuerte para error
        mostrar_alerta_bonita(
            "¡Falta algo! 🔐",
            "La contraseña es necesaria para acceder.\n\n¡Solo un paso más para continuar!",
            "warning"
        )
        entry_pass.focus()
        return False, None
    
    # --- Validar usando la base de datos ---
    try:
        print(f"🔐 Intentando autenticar usuario: {usuario}")
        usuario_verificado = obtener_usuario_por_credenciales(usuario, clave)
        
        if usuario_verificado:
            print(f"✅ Autenticación exitosa para {usuario_verificado['usuario']}")
            # Convertir la información del usuario al formato esperado por el sistema
            datos_usuario = {
                'usuario': usuario_verificado['usuario'],
                'permisos': usuario_verificado['rol'].lower(),  # admin, gerente, vendedor
                'rol_completo': usuario_verificado['rol'],  # Administrador, Gerente, Vendedor
                'id': usuario_verificado['id'],
                'estado': usuario_verificado['estado']
            }
            return True, datos_usuario
        else:
            print(f"❌ Autenticación fallida para usuario: {usuario}")
            # Si no se encuentra el usuario con esas credenciales
            user_frame.config(bg="#FF8A80", bd=3) # Rojo/rosa suave para error
            pass_frame.config(bg="#FF8A80", bd=3) # Rojo/rosa suave para error
            mostrar_alerta_bonita(
                "Credenciales incorrectas 🔒",
                "Usuario o contraseña no coinciden.\n\n¡Verifica tus datos e inténtalo de nuevo!",
                "error"
            )
            entry_user.focus()
            entry_user.select_range(0, tk.END)
            return False, None
            
    except Exception as e:
        print(f"❌ Error durante la autenticación: {e}")
        mostrar_alerta_bonita(
            "Error del sistema 🛠️",
            "Ocurrió un error al verificar las credenciales.\n\n¡Por favor, inténtalo de nuevo!",
            "error"
        )
        return False, None

def _iniciar_flujo_principal(datos_usuario, usuario_actual):
    """
    Función auxiliar para manejar la transición a la siguiente ventana.
    """
    # 1. Destruimos la ventana de login ANTES de llamar al siguiente módulo.
    ventana.destroy()
    # 2. Mostramos la pantalla de carga, y guardamos la referencia en los datos del usuario.
    datos_usuario['ventana_carga'] = mostrar_carga(nombre=usuario_actual, usuario_info=datos_usuario)
    # 3. Iniciamos el dashboard principal.
    menu_inicio.iniciar_dashboard(usuario_actual, datos_usuario)

def validar_usuario(event=None):
    """
    Función principal de validación.
    Llama a validar_campos y, si las credenciales son correctas,
    inicia la transición al dashboard.
    """
    es_valido, datos_usuario = validar_campos()
    
    if not es_valido:
        return

    usuario_actual = datos_usuario['usuario'].capitalize()

    # Mostrar confirmación exitosa
    mostrar_alerta_bonita(
        "¡Bienvenida! ✨",
        f"Hola {usuario_actual}!\n\nAcceso concedido como {datos_usuario['rol_completo']}\nIniciando sistema...",
        "success"
    )
    
    # --- Lógica de transición corregida ---
    # Llamamos a la función auxiliar después de un breve retraso.
    # Esto evita el error de sintaxis del lambda con múltiples sentencias.
    ventana.after(1500, lambda: _iniciar_flujo_principal(datos_usuario, usuario_actual))

def limpiar_campos():
    """Limpiar campos de entrada"""
    usuario_var.set("")
    pass_var.set("")
    user_frame.config(bg="#F3E5F5", bd=2) # Morado muy claro
    pass_frame.config(bg="#F3E5F5", bd=2) # Morado muy claro
    entry_user.focus()

def mostrar_info_usuarios():
    """Muestra información sobre usuarios disponibles (solo para desar
    
    lo/demo)"""
    mensaje = """Usuarios disponibles en el sistema:
    
👤 admin / admin123 (Administrador)
👤 eduardo / 2121 (Administrador) 
👤 andres / 2180 (Vendedor)
👤 gerente / manager (Gerente)

Los usuarios se gestionan desde el menú principal."""
    
    mostrar_alerta_bonita(
        "Información de Usuarios 👥",
        mensaje,
        "warning"
    )

def on_enter_button(event):
    event.widget.config(bg="#C2185B") # Rosa oscuro al pasar el ratón

def on_leave_button(event):
    event.widget.config(bg="#E91E63") # Rosa brillante

def on_enter_clear(event):
    event.widget.config(bg="#7B1FA2") # Morado más oscuro al pasar el ratón

def on_leave_clear(event):
    event.widget.config(bg="#AB47BC") # Morado más suave

def on_enter_info(event):
    event.widget.config(bg="#5E35B1") # Morado más oscuro para info

def on_leave_info(event):
    event.widget.config(bg="#7E57C2") # Morado medio

# Inicializar sistema al arrancar
inicializar_sistema()

# 🖼️ Ventana principal
ventana = tk.Tk()
ventana.title("VmPOS - Centro de Copiado y Papelería")
ventana.geometry("900x500")
ventana.configure(bg="#F8BBD0") # Rosa claro como fondo principal
ventana.resizable(False, False)

# Centrar ventana
ventana.update_idletasks()
x = (ventana.winfo_screenwidth() // 2) - (900 // 2)
y = (ventana.winfo_screenheight() // 2) - (500 // 2)
ventana.geometry(f"900x500+{x}+{y}")

# 🎨 Marco principal con colores combinados
main_frame = tk.Frame(ventana, bg="#FCE4EC") # Rosa muy claro para el marco principal
main_frame.pack(fill="both", expand=True, padx=20, pady=20)

# 📄 Sección izquierda - Información del negocio
left_frame = tk.Frame(main_frame, bg="#E1BEE7", width=400) # Lavanda claro
left_frame.pack(side="left", fill="y", padx=(0, 10))
left_frame.pack_propagate(False)

# Header con iconos de papelería
header_frame = tk.Frame(left_frame, bg="#AB47BC", height=80) # Morado vibrante
header_frame.pack(fill="x", pady=(0, 20))
header_frame.pack_propagate(False)

# Iconos creativos para papelería
icons_text = "📄 ✂️ 📎 🖊️ 📚"
tk.Label(header_frame, text=icons_text, font=("Segoe UI Emoji", 20), 
         bg="#AB47BC", fg="white").pack(pady=15)

# Logo y nombre del negocio
tk.Label(left_frame, text="VmPOS", font=("Segoe UI", 32, "bold"), 
         bg="#E1BEE7", fg="#4A148C").pack(pady=(10, 5)) # Morado oscuro para texto principal

tk.Label(left_frame, text="CENTRO DE COPIADO", font=("Segoe UI", 15, "bold"), 
         bg="#E1BEE7", fg="#880E4F").pack() # Rosa oscuro para texto secundario

tk.Label(left_frame, text="& PAPELERÍA", font=("Segoe UI", 15, "bold"), 
         bg="#E1BEE7", fg="#880E4F").pack(pady=(0, 20)) # Rosa oscuro

# Servicios ofrecidos
services_frame = tk.Frame(left_frame, bg="#E1BEE7")
services_frame.pack(pady=10)

services = [
    "📋 Fotocopias a color y B/N",
    "🖨️ Impresiones profesionales", 
    "📘 Anillados y empastados",
    "✏️ Útiles escolares y oficina",
    "📱 Recargas y servicios"
]

for service in services:
    tk.Label(services_frame, text=service, font=("Segoe UI", 11), 
             bg="#E1BEE7", fg="#4A148C", anchor="w").pack(fill="x", pady=3) # Morado oscuro para servicios

# Información de contacto
contact_frame = tk.Frame(left_frame, bg="#AB47BC") # Morado vibrante
contact_frame.pack(side="bottom", fill="x", pady=(20, 0))

tk.Label(contact_frame, text="📍 Puerto Colombia", font=("Segoe UI", 12, "bold"), 
         bg="#AB47BC", fg="white").pack(pady=8)
tk.Label(contact_frame, text=f"📞 {telefono}", font=("Segoe UI", 12, "bold"), 
         bg="#AB47BC", fg="#FFEB3B").pack(pady=(0, 12)) # Amarillo brillante para contacto

# 🔐 Sección derecha - Login
right_frame = tk.Frame(main_frame, bg="white", width=450)
right_frame.pack(side="right", fill="y")
right_frame.pack_propagate(False)

# Header del login
login_header = tk.Frame(right_frame, bg="#FF80AB", height=100) # Rosa fuerte
login_header.pack(fill="x")
login_header.pack_propagate(False)

tk.Label(login_header, text="🔐", font=("Segoe UI Emoji", 32), 
         bg="#FF80AB", fg="white").pack(pady=(12, 3))
tk.Label(login_header, text="ACCESO AL SISTEMA", font=("Segoe UI", 16, "bold"), 
         bg="#FF80AB", fg="white").pack()

# Contenido del login
login_content = tk.Frame(right_frame, bg="white")
login_content.pack(expand=True, fill="both", padx=40, pady=25)

tk.Label(login_content, text="Inicia sesión para continuar ✨", 
         font=("Segoe UI", 13), bg="white", fg="#616161").pack(pady=(0, 25)) # Gris oscuro

# Variables para los campos
usuario_var = tk.StringVar()
pass_var = tk.StringVar()

# Campo usuario
tk.Label(login_content, text="👤 USUARIO", font=("Segoe UI", 11, "bold"), 
         bg="white", fg="#424242", anchor="w").pack(fill="x", pady=(0, 8)) # Gris muy oscuro

user_frame = tk.Frame(login_content, bg="#F3E5F5", bd=2, relief="solid") # Morado muy claro
user_frame.pack(fill="x", pady=(0, 20))

entry_user = tk.Entry(user_frame, textvariable=usuario_var, font=("Segoe UI", 13), 
                      bg="#F3E5F5", bd=0, fg="#424242")
entry_user.pack(fill="x", padx=12, pady=10)

# Campo contraseña
tk.Label(login_content, text="🔒 CONTRASEÑA", font=("Segoe UI", 11, "bold"), 
         bg="white", fg="#424242", anchor="w").pack(fill="x", pady=(0, 8)) # Gris muy oscuro

pass_frame = tk.Frame(login_content, bg="#F3E5F5", bd=2, relief="solid") # Morado muy claro
pass_frame.pack(fill="x", pady=(0, 25))

entry_pass = tk.Entry(pass_frame, textvariable=pass_var, font=("Segoe UI", 13), 
                      bg="#F3E5F5", bd=0, fg="#424242", show="*") # El atributo show="*" oculta los caracteres por seguridad.
entry_pass.pack(fill="x", padx=12, pady=10)

# Botones personalizados
btn_login = tk.Button(login_content, text="🚀 INICIAR SESIÓN", 
                      font=("Segoe UI", 13, "bold"), bg="#E91E63", fg="white", # Rosa brillante
                      bd=0, pady=12, cursor="hand2", command=validar_usuario,
                      activebackground="#C2185B", relief="flat") # Rosa oscuro para activo
btn_login.pack(fill="x", pady=(0, 12))

# Marco para botones secundarios
buttons_frame = tk.Frame(login_content, bg="white")
buttons_frame.pack(fill="x", pady=(0, 10))

# Fila superior de botones
buttons_row1 = tk.Frame(buttons_frame, bg="white")
buttons_row1.pack(fill="x", pady=(0, 8))

btn_clear = tk.Button(buttons_row1, text="🧹 LIMPIAR", 
                      font=("Segoe UI", 10, "bold"), bg="#AB47BC", fg="white", # Morado más suave
                      bd=0, pady=8, cursor="hand2", command=limpiar_campos,
                      relief="flat")
btn_clear.pack(side="left", expand=True, fill="x", padx=(0, 5))

btn_info = tk.Button(buttons_row1, text="👥 INFO", 
                     font=("Segoe UI", 10, "bold"), bg="#7E57C2", fg="white", # Morado medio
                     bd=0, pady=8, cursor="hand2", command=mostrar_info_usuarios,
                     relief="flat")
btn_info.pack(side="right", expand=True, fill="x", padx=(5, 0))

# Efectos hover para botones
btn_login.bind("<Enter>", on_enter_button)
btn_login.bind("<Leave>", on_leave_button)
btn_clear.bind("<Enter>", on_enter_clear)
btn_clear.bind("<Leave>", on_leave_clear)
btn_info.bind("<Enter>", on_enter_info)
btn_info.bind("<Leave>", on_leave_info)

# Footer con información de versión
footer_frame = tk.Frame(right_frame, bg="#AB47BC", height=70) # Morado más suave
footer_frame.pack(side="bottom", fill="x")
footer_frame.pack_propagate(False)

tk.Label(footer_frame, text="✨ Versión Gratuita 3.1.0 - Base de Datos", 
         font=("Segoe UI", 9, "bold"), bg="#AB47BC", fg="white").pack(pady=(10, 2))
tk.Label(footer_frame, text="💎 Versión PRO disponible con lector de código", 
         font=("Segoe UI", 8), bg="#AB47BC", fg="#FFEB3B").pack() # Amarillo brillante
tk.Label(footer_frame, text="🎯 Sistema de usuarios mejorado", 
         font=("Segoe UI", 8), bg="#AB47BC", fg="#FFEB3B").pack(pady=(0, 8)) # Amarillo brillante

# 🎯 Eventos de teclado
ventana.bind("<Return>", validar_usuario)
ventana.bind("<Escape>", lambda e: limpiar_campos())

# Focus inicial en el campo usuario
entry_user.focus()

# --- Punto de entrada principal para el inicio de sesión ---
if __name__ == "__main__":
    ventana.mainloop()