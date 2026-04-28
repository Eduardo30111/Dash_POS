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
import sys
import os
import webbrowser
from urllib.parse import quote

# Soporte: WhatsApp (+57 320 771 6590)
_WHATSAPP_AYUDA = "573207716590"
_WHATSAPP_MSG_DEFAULT = "Hola, necesito ayuda con VmPOS."

# Evita UnicodeEncodeError en consola Windows (emojis en prints de otros módulos)
if sys.platform == "win32":
    for stream in (getattr(sys, "stdout", None), getattr(sys, "stderr", None)):
        if stream and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass

# Configuración de rutas para PyInstaller

if getattr(sys, 'frozen', False):
    # Si está ejecutándose como ejecutable
    BASE_DIR = sys._MEIPASS
else:
    # Si está ejecutándose como script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Agregar directorios al path
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'interface'))
sys.path.insert(0, os.path.join(BASE_DIR, 'modules'))

try:
    from paths import ensure_runtime_databases
    ensure_runtime_databases()
except ImportError:
    pass

from layout_responsive import centrar_ventana
from ui_theme import T, F_BODY, F_BODY_B, F_HEAD, F_SMALL, F_SUB, F_TITLE

# Importaciones con manejo de errores
try:
    import menu_inicio
except ImportError as e:
    print(f"Error importando menu_inicio: {e}")
    menu_inicio = None

try:
    from pantalla_carga import mostrar_carga
except ImportError as e:
    print(f"Error importando pantalla_carga: {e}")
    def mostrar_carga(nombre="Usuario", usuario_info=None):
        print(f"Pantalla de carga no disponible para {nombre}")
        return None

try:
    from usuarios_db import (
        obtener_usuario_por_credenciales, 
        crear_tablas_iniciales,
        inicializar_admin_default
    )
except ImportError as e:
    print(f"Error importando usuarios_db: {e}")
    def obtener_usuario_por_credenciales(usuario, password):
        return None
    def crear_tablas_iniciales():
        print("crear_tablas_iniciales no disponible (fallo al importar usuarios_db)")
    def inicializar_admin_default():
        print("inicializar_admin_default no disponible (fallo al importar usuarios_db)")

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
    alerta.title("Notificación")
    alerta.configure(bg=T.BG_APP)
    alerta.resizable(False, False)
    alerta.grab_set()
    centrar_ventana(alerta, 400, 280)
    
    if tipo == "error":
        color_header = T.DANGER
        icono = "⚠"
        color_boton = T.DANGER
    elif tipo == "warning":
        color_header = T.WARN
        icono = "!"
        color_boton = T.WARN
    else:
        color_header = T.SUCCESS
        icono = "✓"
        color_boton = T.SUCCESS
    
    main_frame = tk.Frame(alerta, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
    main_frame.pack(fill="both", expand=True, padx=16, pady=16)
    
    header_frame = tk.Frame(main_frame, bg=color_header, height=72)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)
    
    tk.Label(header_frame, text=icono, font=("Segoe UI", 22, "bold"), bg=color_header, fg=T.WHITE).pack(pady=(12, 2))
    tk.Label(header_frame, text=titulo, font=F_SUB, bg=color_header, fg=T.WHITE).pack()
    
    content_frame = tk.Frame(main_frame, bg=T.BG_CARD)
    content_frame.pack(expand=True, fill="both", padx=24, pady=20)
    
    tk.Label(content_frame, text=mensaje, font=F_BODY, 
             bg=T.BG_CARD, fg=T.TEXT, wraplength=300, justify="center").pack(expand=True)
    
    def cerrar_alerta():
        alerta.destroy()
    
    btn_cerrar = tk.Button(content_frame, text="Aceptar", 
                             font=F_BODY_B, bg=color_boton, fg=T.WHITE,
                             bd=0, pady=10, cursor="hand2", command=cerrar_alerta,
                             activebackground=T.TEXT, activeforeground=T.WHITE,
                             relief="flat", width=18)
    btn_cerrar.pack(pady=(12, 0))
    
    def on_enter(e):
        btn_cerrar.config(bg=T.ACCENT_HOVER if tipo == "success" else T.TEXT)
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
    user_frame.config(bg=T.INPUT_BG_ALT, bd=1, highlightbackground=T.INPUT_BORDER, highlightthickness=1)
    pass_frame.config(bg=T.INPUT_BG_ALT, bd=1, highlightbackground=T.INPUT_BORDER, highlightthickness=1)
    
    if not usuario:
        user_frame.config(bg=T.DANGER_BG, bd=1, highlightbackground=T.DANGER, highlightthickness=1)
        mostrar_alerta_bonita(
            "¡Ups! Campo vacío 😊",
            "Por favor, ingresa tu nombre de usuario.\n\n¡No te olvides de este importante detalle!",
            "warning"
        )
        entry_user.focus()
        return False, None
    
    if not clave:
        pass_frame.config(bg=T.DANGER_BG, bd=1, highlightbackground=T.DANGER, highlightthickness=1)
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
            user_frame.config(bg=T.DANGER_BG, bd=1, highlightbackground=T.DANGER, highlightthickness=1)
            pass_frame.config(bg=T.DANGER_BG, bd=1, highlightbackground=T.DANGER, highlightthickness=1)
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
    try:
        # 1. Destruimos la ventana de login ANTES de llamar al siguiente módulo.
        ventana.destroy()
        
        # 2. Mostramos la pantalla de carga con parámetros corregidos
        print(f"📺 Mostrando pantalla de carga para {usuario_actual}")
        mostrar_carga(usuario_actual, datos_usuario)
        
        # 3. Iniciamos el dashboard principal (si está disponible)
        if menu_inicio:
            print(f"🚀 Iniciando dashboard para {usuario_actual}")
            menu_inicio.iniciar_dashboard(usuario_actual, datos_usuario)
        else:
            print("❌ Dashboard no disponible")
            
    except Exception as e:
        print(f"❌ Error en flujo principal: {e}")

def validar_usuario(event=None):
    """
    Función principal de validación.
    Llama a validar_campos y, si las credenciales son correctas,
    inicia la transición al dashboard.
    """
    es_valido, datos_usuario = validar_campos()
    
    if not es_valido:
        return

    try:
        from license_remote import remote_license_screening

        allow_lr, tit_lr, msg_lr = remote_license_screening()
        if not allow_lr:
            # Si la licencia fue desactivada en el dashboard, permitir acceso limitado:
            # entra al menú principal, pero módulos bloqueados y aviso de renovación.
            if (tit_lr or "").strip().lower() == "acceso desactivado":
                if isinstance(datos_usuario, dict):
                    datos_usuario["license_limited"] = True
                    datos_usuario["license_notice_title"] = "Tu licencia ha vencido"
                    datos_usuario["license_notice_message"] = (
                        "Tu licencia ha vencido. Si quieres renovarla, escríbenos por WhatsApp."
                    )
                    datos_usuario["license_notice_whatsapp"] = "3207716590"
            else:
                mostrar_alerta_bonita(tit_lr or "VmPOS", msg_lr, "error")
                return
    except Exception as ex_lr:
        print(f"VmPOS: verificación remota omitida o error: {ex_lr}")

    usuario_actual = datos_usuario['usuario'].capitalize()

    # Mostrar confirmación exitosa
    mostrar_alerta_bonita(
        "¡Bienvenida! ✨",
        f"Hola {usuario_actual}!\n\nAcceso concedido como {datos_usuario['rol_completo']}\nIniciando sistema...",
        "success"
    )
    
    # --- Lógica de transición corregida ---
    # Llamamos a la función auxiliar después de un breve retraso.
    ventana.after(1500, lambda: _iniciar_flujo_principal(datos_usuario, usuario_actual))

def limpiar_campos():
    """Limpiar campos de entrada"""
    user_var.set("")
    pass_var.set("")
    user_frame.config(bg=T.INPUT_BG_ALT, bd=1, highlightbackground=T.INPUT_BORDER, highlightthickness=1)
    pass_frame.config(bg=T.INPUT_BG_ALT, bd=1, highlightbackground=T.INPUT_BORDER, highlightthickness=1)
    entry_user.focus()

def abrir_ayuda_whatsapp():
    """Abre una conversación de WhatsApp con soporte (navegador o app)."""
    try:
        url = f"https://wa.me/{_WHATSAPP_AYUDA}?text={quote(_WHATSAPP_MSG_DEFAULT)}"
        webbrowser.open(url)
    except Exception as e:
        messagebox.showerror(
            "Ayuda",
            f"No se pudo abrir WhatsApp automáticamente.\n\n"
            f"Escribe al nombre: Cliente_\n\n({e})",
        )

def on_enter_button(event):
    event.widget.config(bg=T.ACCENT_HOVER)

def on_leave_button(event):
    event.widget.config(bg=T.ACCENT)

def on_enter_clear(event):
    event.widget.config(bg=T.NAV_BAR_BTN_HOVER)

def on_leave_clear(event):
    event.widget.config(bg=T.NAV_BAR_BTN)

def on_enter_info(event):
    event.widget.config(bg=T.SIDEBAR_HOVER)

def on_leave_info(event):
    event.widget.config(bg=T.SIDEBAR)

# Inicializar sistema al arrancar
inicializar_sistema()

# 🖼️ Ventana principal
ventana = tk.Tk()
ventana.title("VmPOS · Inicio de sesión")
ventana.configure(bg=T.BG_APP)
ventana.resizable(True, True)
ventana.minsize(720, 560)
ventana.update_idletasks()
_sw = ventana.winfo_screenwidth()
_sh = ventana.winfo_screenheight()
_w = min(1020, max(720, int(_sw * 0.88)))
_h = min(820, max(560, int(_sh * 0.82)))
centrar_ventana(ventana, _w, _h)

main_frame = tk.Frame(ventana, bg=T.BG_APP)
main_frame.pack(fill="both", expand=True, padx=32, pady=24)

left_frame = tk.Frame(main_frame, bg=T.SIDEBAR, width=400)
left_frame.pack(side="left", fill="y", padx=(0, 16))
left_frame.pack_propagate(False)

header_frame = tk.Frame(left_frame, bg=T.SIDEBAR, height=64)
header_frame.pack(fill="x")
header_frame.pack_propagate(False)
tk.Label(
    header_frame,
    text="VmPOS",
    font=F_TITLE,
    bg=T.SIDEBAR,
    fg=T.WHITE,
    anchor="w",
).pack(side="left", padx=24, pady=20)

tk.Label(
    left_frame,
    text="Centro de copiado",
    font=F_HEAD,
    bg=T.SIDEBAR,
    fg=T.WHITE,
    anchor="w",
).pack(anchor="w", padx=24, pady=(8, 0))
tk.Label(
    left_frame,
    text="y papelería",
    font=F_SUB,
    bg=T.SIDEBAR,
    fg=T.HEADER_TEXT_DIM,
    anchor="w",
).pack(anchor="w", padx=24, pady=(0, 20))

services_frame = tk.Frame(left_frame, bg=T.SIDEBAR)
services_frame.pack(fill="x", padx=20, pady=8)

services = [
    "Fotocopias color y B/N",
    "Impresiones y anillados",
    "Útiles escolares y oficina",
    "Material de arte y manualidades",
]

for service in services:
    tk.Label(
        services_frame,
        text="· " + service,
        font=F_BODY,
        bg=T.SIDEBAR,
        fg=T.HEADER_TEXT_DIM,
        anchor="w",
    ).pack(fill="x", pady=4)

contact_frame = tk.Frame(left_frame, bg=T.SIDEBAR_HOVER)
contact_frame.pack(side="bottom", fill="x", pady=(24, 0))

tk.Label(
    contact_frame,
    text="Puerto Colombia",
    font=F_BODY_B,
    bg=T.SIDEBAR_HOVER,
    fg=T.WHITE,
).pack(anchor="w", padx=20, pady=(16, 4))
tk.Label(
    contact_frame,
    text=telefono,
    font=F_BODY,
    bg=T.SIDEBAR_HOVER,
    fg=T.ACCENT_SOFT,
).pack(anchor="w", padx=20, pady=(0, 16))

right_frame = tk.Frame(main_frame, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
right_frame.pack(side="right", fill="both", expand=True)
right_frame.pack_propagate(False)

login_header = tk.Frame(right_frame, bg=T.HEADER_BAR, height=88)
login_header.pack(fill="x")
login_header.pack_propagate(False)

tk.Label(login_header, text="Acceso al sistema", font=F_HEAD, bg=T.HEADER_BAR, fg=T.WHITE).pack(
    side="left", padx=28, pady=28
)

login_content = tk.Frame(right_frame, bg=T.BG_CARD)
login_content.pack(expand=True, fill="both", padx=40, pady=28)

tk.Label(
    login_content,
    text="Inicia sesión con tu usuario corporativo",
    font=F_BODY,
    bg=T.BG_CARD,
    fg=T.TEXT_MUTED,
).pack(anchor="w", pady=(0, 20))

usuario_var = tk.StringVar()
pass_var = tk.StringVar()

tk.Label(login_content, text="Usuario", font=F_BODY_B, bg=T.BG_CARD, fg=T.TEXT, anchor="w").pack(fill="x", pady=(0, 6))

user_frame = tk.Frame(login_content, bg=T.INPUT_BG_ALT, highlightbackground=T.INPUT_BORDER, highlightthickness=1)
user_frame.pack(fill="x", pady=(0, 16))

entry_user = tk.Entry(
    user_frame,
    textvariable=usuario_var,
    font=F_SUB,
    bg=T.INPUT_BG,
    bd=0,
    fg=T.TEXT,
    insertbackground=T.TEXT,
    highlightthickness=0,
)
entry_user.pack(fill="x", padx=14, pady=12)

tk.Label(login_content, text="Contraseña", font=F_BODY_B, bg=T.BG_CARD, fg=T.TEXT, anchor="w").pack(
    fill="x", pady=(0, 6)
)

pass_frame = tk.Frame(login_content, bg=T.INPUT_BG_ALT, highlightbackground=T.INPUT_BORDER, highlightthickness=1)
pass_frame.pack(fill="x", pady=(0, 24))

entry_pass = tk.Entry(
    pass_frame,
    textvariable=pass_var,
    font=F_SUB,
    bg=T.INPUT_BG,
    bd=0,
    fg=T.TEXT,
    show="*",
    insertbackground=T.TEXT,
    highlightthickness=0,
)
entry_pass.pack(fill="x", padx=14, pady=12)

btn_login = tk.Button(
    login_content,
    text="Iniciar sesión",
    font=F_BODY_B,
    bg=T.ACCENT,
    fg=T.WHITE,
    bd=0,
    pady=12,
    cursor="hand2",
    command=validar_usuario,
    activebackground=T.ACCENT_HOVER,
    activeforeground=T.WHITE,
    relief="flat",
)
btn_login.pack(fill="x", pady=(0, 12))

buttons_frame = tk.Frame(login_content, bg=T.BG_CARD)
buttons_frame.pack(fill="x", pady=(0, 8))

buttons_row1 = tk.Frame(buttons_frame, bg=T.BG_CARD)
buttons_row1.pack(fill="x", pady=(0, 8))

btn_clear = tk.Button(
    buttons_row1,
    text="Limpiar",
    font=F_BODY_B,
    bg=T.NAV_BAR_BTN,
    fg=T.WHITE,
    bd=0,
    pady=10,
    cursor="hand2",
    command=limpiar_campos,
    activebackground=T.NAV_BAR_BTN_HOVER,
    relief="flat",
)
btn_clear.pack(side="left", expand=True, fill="x", padx=(0, 6))

btn_info = tk.Button(
    buttons_row1,
    text="Ayuda",
    font=F_BODY_B,
    bg=T.SIDEBAR,
    fg=T.WHITE,
    bd=0,
    pady=10,
    cursor="hand2",
    command=abrir_ayuda_whatsapp,
    activebackground=T.SIDEBAR_HOVER,
    relief="flat",
)
btn_info.pack(side="right", expand=True, fill="x", padx=(6, 0))

btn_login.bind("<Enter>", on_enter_button)
btn_login.bind("<Leave>", on_leave_button)
btn_clear.bind("<Enter>", on_enter_clear)
btn_clear.bind("<Leave>", on_leave_clear)
btn_info.bind("<Enter>", on_enter_info)
btn_info.bind("<Leave>", on_leave_info)

footer_frame = tk.Frame(right_frame, bg=T.FOOTER, height=56)
footer_frame.pack(side="bottom", fill="x")
footer_frame.pack_propagate(False)

tk.Label(
    footer_frame,
    text="VmPOS · versión de demostración",
    font=F_SMALL,
    bg=T.FOOTER,
    fg=T.HEADER_TEXT_DIM,
).pack(pady=18)

# 🎯 Eventos de teclado
ventana.bind("<Return>", validar_usuario)
ventana.bind("<Escape>", lambda e: limpiar_campos())

# Focus inicial en el campo usuario
entry_user.focus()

# --- Punto de entrada principal para el inicio de sesión ---
if __name__ == "__main__":
    ventana.mainloop()