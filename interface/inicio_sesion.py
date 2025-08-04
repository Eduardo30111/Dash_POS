import tkinter as tk
from tkinter import ttk
import menu_inicio
from pantalla_carga import mostrar_carga
from tkinter import messagebox # Ensure messagebox is explicitly imported

# Import the authentication function from usuarios_db
from usuarios_db import obtener_usuario_por_credenciales

# --- Variables necesarias (telefono es estático) ---
telefono = "+573215545788" # <--- ¡HE VUELTO A PONER EL TELÉFONO AQUÍ!
# --- Las variables de prueba originales (usuario_valido, clave_valida) ya no se usan para la validación ---

# 🚨 Sistema de alertas personalizadas (Mantener funcionalidad, quizás ajustar colores de alerta si es necesario)
def mostrar_alerta_bonita(titulo, mensaje, tipo="error"):
    alerta = tk.Toplevel()
    alerta.title("💫 Notificación")
    alerta.geometry("400x280")
    alerta.configure(bg="#FCE4EC") # Rosa muy claro de fondo de alerta
    alerta.resizable(False, False)
    alerta.grab_set()   # Hacer modal
    
    # Centrar alerta
    alerta.update_idletasks()
    x = (alerta.winfo_screenwidth() // 2) - (400 // 2)
    y = (alerta.winfo_screenheight() // 2) - (280 // 2)
    alerta.geometry(f"400x280+{x}+{y}")
    
    # Colores según tipo (ajustados para el nuevo estilo)
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
    
    # Auto-cerrar después de 4 segundos
    alerta.after(3000, cerrar_alerta)
    
    # Focus y tecla Enter
    btn_cerrar.focus()
    alerta.bind("<Return>", lambda e: cerrar_alerta())

def validar_campos():
    """Validación elegante de campos"""
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
        return False
    
    if not clave:
        pass_frame.config(bg="#FFCDD2", bd=3) # Rosa más fuerte para error
        mostrar_alerta_bonita(
            "¡Falta algo! 🔐",
            "La contraseña es necesaria para acceder.\n\n¡Solo un paso más para continuar!",
            "warning"
        )
        entry_pass.focus()
        return False
    
    # --- Validar contra la base de datos ---
    usuario_encontrado = obtener_usuario_por_credenciales(usuario, clave)
    
    if not usuario_encontrado:
        # Si no se encuentra el usuario con esas credenciales
        user_frame.config(bg="#FF8A80", bd=3) # Rojo/rosa suave para error
        pass_frame.config(bg="#FF8A80", bd=3) # Rojo/rosa suave para error
        mostrar_alerta_bonita(
            "Credenciales incorrectas 🤔",
            "Usuario o contraseña no coinciden.\n\n¡Verifica tus datos e inténtalo de nuevo!",
            "error"
        )
        entry_user.focus()
        entry_user.select_range(0, tk.END)
        return False
    
    # Si las credenciales son correctas, el usuario_encontrado no es None
    return True

def validar_usuario(event=None):
    """Función principal de validación"""
    if validar_campos():
        # Obtener el nombre de usuario (ya validado) para mostrar en el mensaje
        usuario_actual = usuario_var.get().capitalize()

        # Mostrar confirmación exitosa
        mostrar_alerta_bonita(
            "¡Bienvenida! ✨",
            f"Hola {usuario_actual}!\n\nAcceso concedido, iniciando sistema...",
            "success"
        )
        
        # Cerrar ventana después de un momento
        ventana.after(2000, lambda: [
            ventana.destroy(),
            mostrar_carga(nombre=usuario_actual),
            menu_inicio.iniciar_dashboard(usuario_actual)
        ])

def limpiar_campos():
    """Limpiar campos de entrada"""
    usuario_var.set("")
    pass_var.set("")
    user_frame.config(bg="#F3E5F5", bd=2) # Morado muy claro
    pass_frame.config(bg="#F3E5F5", bd=2) # Morado muy claro
    entry_user.focus()

def on_enter_button(event):
    event.widget.config(bg="#C2185B") # Rosa oscuro al pasar el ratón

def on_leave_button(event):
    event.widget.config(bg="#E91E63") # Rosa brillante

def on_enter_register(event):
    event.widget.config(bg="#6A1B9A") # Morado oscuro al pasar el ratón

def on_leave_register(event):
    event.widget.config(bg="#9C27B0") # Morado

def on_enter_clear(event):
    event.widget.config(bg="#7B1FA2") # Morado más oscuro al pasar el ratón

def on_leave_clear(event):
    event.widget.config(bg="#AB47BC") # Morado más suave

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
                      bg="#F3E5F5", bd=0, fg="#424242", show="*")
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

btn_register = tk.Button(buttons_frame, text="📝 REGISTRAR", 
                          font=("Segoe UI", 10, "bold"), bg="#9C27B0", fg="white", # Morado
                          bd=0, pady=8, cursor="hand2", activebackground="#6A1B9A",
                          relief="flat", width=15) # Morado oscuro para activo
btn_register.pack(side="left", padx=(0, 8))

btn_clear = tk.Button(buttons_frame, text="🧹 LIMPIAR", 
                      font=("Segoe UI", 10, "bold"), bg="#AB47BC", fg="white", # Morado más suave
                      bd=0, pady=8, cursor="hand2", command=limpiar_campos,
                      relief="flat", width=15)
btn_clear.pack(side="right")

# Efectos hover para botones
btn_login.bind("<Enter>", on_enter_button)
btn_login.bind("<Leave>", on_leave_button)
btn_register.bind("<Enter>", on_enter_register)
btn_register.bind("<Leave>", on_leave_register)
btn_clear.bind("<Enter>", on_enter_clear)
btn_clear.bind("<Leave>", on_leave_clear)

# Footer con información de versión
footer_frame = tk.Frame(right_frame, bg="#AB47BC", height=70) # Morado más suave
footer_frame.pack(side="bottom", fill="x")
footer_frame.pack_propagate(False)

tk.Label(footer_frame, text="✨ Versión Gratuita 3.1.0", 
         font=("Segoe UI", 9, "bold"), bg="#AB47BC", fg="white").pack(pady=(10, 2))
tk.Label(footer_frame, text="💎 Versión PRO disponible con lector de código", 
         font=("Segoe UI", 8), bg="#AB47BC", fg="#FFEB3B").pack() # Amarillo brillante
tk.Label(footer_frame, text="🎯 Haz tu aporte y mejora tu sistema", 
         font=("Segoe UI", 8), bg="#AB47BC", fg="#FFEB3B").pack(pady=(0, 8)) # Amarillo brillante

# 🎯 Eventos de teclado
ventana.bind("<Return>", validar_usuario)
ventana.bind("<Escape>", lambda e: limpiar_campos())


# Focus inicial en el campo usuario
entry_user.focus()

ventana.mainloop()
