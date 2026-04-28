# -*- coding: utf-8 -*-
"""
Archivo: usuarios_menu.py
Interfaz de gestión de usuarios para VmPOS.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import os
import sqlite3

# Importar funciones de la base de datos de usuarios
from usuarios_db import (
    crear_tablas_iniciales, insertar_usuario, obtener_usuarios,
    actualizar_usuario_db, eliminar_usuario_db,
    obtener_permisos_por_usuario, MODULOS_DISPONIBLES, hash_password,
    obtener_usuario_por_credenciales, inicializar_admin_default,
    migrar_usuarios_existentes
)

from layout_responsive import crear_cuerpo_modulo_scroll, modulo_scroll_finalizar
from ui_theme import T, F_TITLE, F_HEAD, F_BODY, F_BODY_B, F_SMALL, F_STAT, style_ttk_treeview_pos

# 🌐 Variables globales para los widgets de la interfaz
entradas = {}
tabla = None
ventana_usuarios = None
rol_var = None
estado_var = None
id_usuario_seleccionado = None

def inicializar_sistema_usuarios():
    """Inicializa el sistema de usuarios creando tablas y datos por defecto."""
    print("🔧 Inicializando sistema de usuarios...")
    crear_tablas_iniciales()
    inicializar_admin_default()
    
    # Verificar si hay usuarios en la base de datos
    usuarios = obtener_usuarios()
    if len(usuarios) == 0:
        print("📥 Base de datos vacía, cargando datos de ejemplo...")
        cargar_datos_ejemplo()
    else:
        print(f"✅ Se encontraron {len(usuarios)} usuarios en la base de datos.")

def cargar_datos_ejemplo():
    """Carga datos de ejemplo en la base de datos."""
    usuarios_ejemplo = [
        {"usuario": "admin", "password": "admin123", "rol": "Administrador", "estado": "Activo"},
        {"usuario": "eduardo", "password": "2121", "rol": "Administrador", "estado": "Activo"},
        {"usuario": "andres", "password": "2180", "rol": "Vendedor", "estado": "Activo"},
        {"usuario": "gerente", "password": "manager", "rol": "Gerente", "estado": "Activo"},
        {"usuario": "vendedor1", "password": "pass123", "rol": "Vendedor", "estado": "Activo"}
    ]
    
    for user in usuarios_ejemplo:
        resultado = insertar_usuario(
            user["usuario"],
            user["password"],
            user["rol"],
            user["estado"]
        )
        if resultado:
            print(f"✅ Usuario '{user['usuario']}' creado correctamente.")
        else:
            print(f"⚠️ Usuario '{user['usuario']}' ya existe o hubo un error.")

def actualizar_tabla():
    """
    Actualiza la tabla con los datos más recientes de la base de datos.
    """
    global tabla
    
    if not tabla:
        return
    
    # Limpiar tabla actual
    for item in tabla.get_children():
        tabla.delete(item)

    # Obtener usuarios de la base de datos
    usuarios = obtener_usuarios()
    print(f"📋 Cargando {len(usuarios)} usuarios en la tabla.")

    # Insertar los datos en la tabla
    for usuario in usuarios:
        # Formatear las fechas para mejor visualización
        fecha_registro = usuario['fecha_registro']
        if isinstance(fecha_registro, str):
            try:
                # Intentar parsear la fecha si viene como string
                fecha_obj = datetime.fromisoformat(fecha_registro.replace('Z', '+00:00'))
                fecha_formateada = fecha_obj.strftime("%d/%m/%Y %H:%M")
            except:
                fecha_formateada = fecha_registro
        else:
            fecha_formateada = str(fecha_registro) if fecha_registro else "No disponible"
        
        ultimo_acceso = usuario['ultimo_acceso']
        if ultimo_acceso and ultimo_acceso != "Nunca":
            try:
                if isinstance(ultimo_acceso, str):
                    fecha_obj = datetime.fromisoformat(ultimo_acceso.replace('Z', '+00:00'))
                    ultimo_acceso = fecha_obj.strftime("%d/%m/%Y %H:%M")
            except:
                pass
        
        valores = (
            usuario['id'],
            usuario['usuario'],
            usuario['rol'],
            usuario['estado'],
            ultimo_acceso if ultimo_acceso else "Nunca",
            fecha_formateada
        )
        
        tabla.insert("", "end", values=valores)
    
    print("✅ Tabla actualizada correctamente.")

def seleccionar_usuario(event):
    """
    Carga los datos del usuario seleccionado en los campos de edición.
    """
    global id_usuario_seleccionado
    global entradas, rol_var, estado_var

    item_seleccionado = tabla.focus()
    if not item_seleccionado:
        return
    
    try:
        # Obtener los valores de la fila seleccionada
        valores = tabla.item(item_seleccionado, 'values')
        
        if not valores:
            return
        
        # Guardar el ID del usuario seleccionado
        id_usuario_seleccionado = int(valores[0])
        
        # Cargar los valores en los campos de entrada
        entradas['Usuario'].delete(0, tk.END)
        entradas['Usuario'].insert(0, valores[1])
        
        # Limpiar el campo de contraseña por seguridad
        entradas['Password'].delete(0, tk.END)
        entradas['Password'].insert(0, "")  # Campo vacío para nueva contraseña (opcional)
        
        # Establecer rol y estado
        rol_var.set(valores[2])
        estado_var.set(valores[3])
        
        print(f"👤 Usuario seleccionado: {valores[1]} (ID: {id_usuario_seleccionado})")
        
    except Exception as e:
        print(f"❌ Error al seleccionar usuario: {e}")
        messagebox.showerror("Error", f"Error al cargar datos del usuario: {e}")

def guardar_usuario():
    """
    Guarda o actualiza un usuario en la base de datos.
    """
    global id_usuario_seleccionado
    
    usuario = entradas['Usuario'].get().strip()
    password = entradas['Password'].get().strip()
    rol = rol_var.get()
    estado = estado_var.get()
    
    # Validaciones
    if not usuario:
        messagebox.showerror("Error", "El campo Usuario es obligatorio.")
        entradas['Usuario'].focus()
        return
    
    if rol == "Seleccionar" or not rol:
        messagebox.showerror("Error", "Debes seleccionar un rol.")
        return
    
    if estado == "Seleccionar" or not estado:
        messagebox.showerror("Error", "Debes seleccionar un estado.")
        return
    
    try:
        if id_usuario_seleccionado:
            # Actualizar usuario existente
            print(f"🔄 Actualizando usuario con ID: {id_usuario_seleccionado}")
            
            # Si no se proporciona contraseña, no la actualizar
            if password:
                resultado = actualizar_usuario_db(
                    id_usuario_seleccionado, 
                    usuario=usuario, 
                    rol=rol, 
                    estado=estado, 
                    password=password
                )
            else:
                resultado = actualizar_usuario_db(
                    id_usuario_seleccionado, 
                    usuario=usuario, 
                    rol=rol, 
                    estado=estado
                )
            
            if resultado:
                messagebox.showinfo("Éxito", f"Usuario '{usuario}' actualizado correctamente.")
            else:
                messagebox.showerror("Error", "No se pudo actualizar el usuario.")
        else:
            # Crear nuevo usuario
            if not password:
                messagebox.showerror("Error", "La contraseña es obligatoria para un nuevo usuario.")
                entradas['Password'].focus()
                return
            
            print(f"➕ Creando nuevo usuario: {usuario}")
            resultado = insertar_usuario(usuario, password, rol, estado)
            
            if resultado:
                messagebox.showinfo("Éxito", f"Usuario '{usuario}' creado correctamente.")
            else:
                messagebox.showerror("Error", f"No se pudo crear el usuario. Es posible que ya exista.")
        
        # Limpiar campos y actualizar tabla
        limpiar_campos()
        actualizar_tabla()
        
    except Exception as e:
        print(f"❌ Error al guardar usuario: {e}")
        messagebox.showerror("Error de base de datos", f"Ocurrió un error al guardar el usuario:\n{e}")

def eliminar_usuario():
    """
    Elimina el usuario seleccionado de la base de datos.
    """
    global id_usuario_seleccionado
    
    if not id_usuario_seleccionado:
        messagebox.showwarning("Advertencia", "Por favor, selecciona un usuario de la tabla para eliminar.")
        return
    
    # Obtener nombre del usuario para confirmar
    usuario_seleccionado = entradas['Usuario'].get()
    
    # Confirmación
    respuesta = messagebox.askyesno(
        "Confirmar eliminación", 
        f"¿Estás seguro de que quieres eliminar el usuario '{usuario_seleccionado}'?\n\nEsta acción no se puede deshacer."
    )
    
    if not respuesta:
        return
    
    try:
        print(f"🗑️ Eliminando usuario con ID: {id_usuario_seleccionado}")
        resultado = eliminar_usuario_db(id_usuario_seleccionado)
        
        if resultado:
            messagebox.showinfo("Éxito", f"Usuario '{usuario_seleccionado}' eliminado correctamente.")
            limpiar_campos()
            actualizar_tabla()
        else:
            messagebox.showerror("Error", "No se pudo eliminar el usuario.")
            
    except Exception as e:
        print(f"❌ Error al eliminar usuario: {e}")
        messagebox.showerror("Error de base de datos", f"Ocurrió un error al eliminar el usuario:\n{e}")

def limpiar_campos():
    """
    Limpia todos los campos de entrada y restablece la selección.
    """
    global id_usuario_seleccionado
    
    # Limpiar campos de texto
    for campo in ["Usuario", "Password"]:
        if campo in entradas:
            entradas[campo].delete(0, tk.END)
    
    # Restablecer comboboxes
    if rol_var:
        rol_var.set("Seleccionar")
    if estado_var:
        estado_var.set("Seleccionar")

    # Limpiar selección
    id_usuario_seleccionado = None
    
    if tabla and tabla.selection():
        tabla.selection_remove(tabla.selection())
    
    # Focus en el primer campo
    if 'Usuario' in entradas:
        entradas['Usuario'].focus()
    
    print("🧹 Campos limpiados.")

def probar_login():
    """
    Función para probar el sistema de login con las credenciales ingresadas.
    """
    usuario = entradas['Usuario'].get().strip()
    contrasena = entradas['Password'].get().strip()

    if not usuario or not contrasena:
        messagebox.showerror("Error", "Por favor, introduce un usuario y una contraseña para probar.")
        return
        
    print(f"🔐 Probando login para usuario: {usuario}")
    usuario_verificado = obtener_usuario_por_credenciales(usuario, contrasena)

    if usuario_verificado:
        mensaje = f"✅ Login exitoso!\n\n" \
                  f"Usuario: {usuario_verificado['usuario']}\n" \
                  f"Rol: {usuario_verificado['rol']}\n" \
                  f"Estado: {usuario_verificado['estado']}"
        messagebox.showinfo("Login Exitoso", mensaje)
        print(f"✅ Login exitoso para {usuario_verificado['usuario']}")
    else:
        messagebox.showerror("Login Fallido", "❌ Credenciales incorrectas o usuario inactivo.")
        print(f"❌ Login fallido para usuario: {usuario}")

def refrescar_tabla():
    """Refresca la tabla de usuarios."""
    print("🔄 Refrescando tabla...")
    actualizar_tabla()
    messagebox.showinfo("Información", "Tabla actualizada correctamente.")

def iniciar_usuarios(parent=None):
    """
    Función principal que inicializa la ventana de gestión de usuarios.
    """
    global tabla, entradas, ventana_usuarios, rol_var, estado_var

    print("Iniciando ventana de gestión de usuarios...")

    # Inicializar sistema de usuarios
    inicializar_sistema_usuarios()

    if parent is not None:
        ventana_usuarios = tk.Toplevel(parent)
        try:
            ventana_usuarios.transient(parent)
        except tk.TclError:
            pass
    else:
        ventana_usuarios = tk.Tk()
    ventana_usuarios.title("Gestión de Usuarios - VmPOS")
    if parent is not None:
        from navegacion_ventanas import instalar_barra_volver
        instalar_barra_volver(ventana_usuarios, parent)
    else:
        from layout_responsive import configurar_ventana_modulo
        configurar_ventana_modulo(ventana_usuarios, min_w=800, min_h=560, ratio_w=0.9, ratio_h=0.86)
    ventana_usuarios.resizable(True, True)
    ventana_usuarios.configure(bg=T.BG_APP)

    cuerpo = crear_cuerpo_modulo_scroll(ventana_usuarios, bg=T.BG_APP)

    style = ttk.Style()
    style_ttk_treeview_pos(style, T.BG_APP)

    header_frame = tk.Frame(cuerpo, bg=T.POS_HEADER, height=76)
    header_frame.pack(fill=tk.X)
    header_frame.pack_propagate(False)
    hl = tk.Frame(header_frame, bg=T.POS_HEADER)
    hl.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=(12, 14))
    tk.Label(hl, text="Usuarios del sistema", font=F_TITLE, bg=T.POS_HEADER, fg=T.WHITE).pack(anchor="w")
    tk.Label(
        hl,
        text="Cree cuentas, asigne roles y active o desactive el acceso. La contraseña solo se actualiza si escribe una nueva.",
        font=F_SMALL,
        bg=T.POS_HEADER,
        fg=T.HEADER_TEXT_DIM,
        wraplength=820,
        justify="left",
    ).pack(anchor="w", pady=(4, 0))

    main_frame = tk.Frame(cuerpo, bg=T.BG_APP)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)
    main_frame.grid_rowconfigure(1, weight=1)
    main_frame.grid_columnconfigure(0, weight=1)

    form_frame = tk.Frame(main_frame, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
    form_frame.grid(row=0, column=0, sticky="ew", padx=4, pady=(0, 10))
    tk.Frame(form_frame, bg=T.ACCENT, height=3).pack(fill="x")
    tk.Label(form_frame, text="Nuevo o editar usuario", font=F_HEAD, bg=T.BG_CARD, fg=T.TEXT).pack(anchor="w", padx=14, pady=(10, 4))
    form_inner = tk.Frame(form_frame, bg=T.BG_CARD)
    form_inner.pack(fill="x", padx=14, pady=(0, 14))
    
    # Crear grid para el formulario
    campos = ["Usuario", "Password"]
    roles = ["Administrador", "Vendedor"]
    estados = ["Activo", "Inactivo"]
    
    # Variables de control para Comboboxes
    rol_var = tk.StringVar(value="Seleccionar")
    estado_var = tk.StringVar(value="Seleccionar")
    
    tk.Label(form_inner, text="Usuario", font=F_BODY_B, bg=T.BG_CARD, fg=T.TEXT).grid(row=0, column=0, padx=(0, 10), pady=6, sticky="w")
    entrada_usuario = tk.Entry(
        form_inner, font=F_BODY, width=36, relief="flat", bd=0,
        highlightthickness=1, highlightbackground=T.INPUT_BORDER,
    )
    entrada_usuario.grid(row=0, column=1, padx=0, pady=6, sticky="ew", ipady=4)
    entradas["Usuario"] = entrada_usuario

    tk.Label(form_inner, text="Contraseña", font=F_BODY_B, bg=T.BG_CARD, fg=T.TEXT).grid(row=1, column=0, padx=(0, 10), pady=6, sticky="w")
    entrada_password = tk.Entry(
        form_inner, font=F_BODY, width=36, relief="flat", bd=0, show="*",
        highlightthickness=1, highlightbackground=T.INPUT_BORDER,
    )
    entrada_password.grid(row=1, column=1, padx=0, pady=6, sticky="ew", ipady=4)
    entradas["Password"] = entrada_password

    tk.Label(form_inner, text="Rol", font=F_BODY_B, bg=T.BG_CARD, fg=T.TEXT).grid(row=2, column=0, padx=(0, 10), pady=6, sticky="w")
    combo_rol = ttk.Combobox(form_inner, textvariable=rol_var, values=roles, state="readonly", width=34, font=F_BODY)
    combo_rol.grid(row=2, column=1, padx=0, pady=6, sticky="w")

    tk.Label(form_inner, text="Estado", font=F_BODY_B, bg=T.BG_CARD, fg=T.TEXT).grid(row=3, column=0, padx=(0, 10), pady=6, sticky="w")
    combo_estado = ttk.Combobox(form_inner, textvariable=estado_var, values=estados, state="readonly", width=34, font=F_BODY)
    combo_estado.grid(row=3, column=1, padx=0, pady=6, sticky="w")
    form_inner.grid_columnconfigure(1, weight=1)

    botones_frame = tk.Frame(form_inner, bg=T.BG_CARD)
    botones_frame.grid(row=4, column=0, columnspan=2, pady=(12, 0), sticky="w")

    btn_guardar = tk.Button(
        botones_frame, text="Guardar", command=guardar_usuario,
        bg=T.STAT_3, fg=T.WHITE, font=F_BODY_B, relief="flat", padx=14, pady=8, cursor="hand2",
        activebackground=T.POS_BTN_GO_HOVER, activeforeground=T.WHITE,
    )
    btn_guardar.pack(side="left", padx=(0, 6))

    btn_eliminar = tk.Button(
        botones_frame, text="Eliminar", command=eliminar_usuario,
        bg=T.DANGER, fg=T.WHITE, font=F_BODY_B, relief="flat", padx=14, pady=8, cursor="hand2",
        activebackground="#b91c1c", activeforeground=T.WHITE,
    )
    btn_eliminar.pack(side="left", padx=6)

    btn_limpiar = tk.Button(
        botones_frame, text="Limpiar", command=limpiar_campos,
        bg=T.POS_BTN_ALT, fg=T.WHITE, font=F_BODY_B, relief="flat", padx=14, pady=8, cursor="hand2",
        activebackground=T.TEXT_MUTED, activeforeground=T.WHITE,
    )
    btn_limpiar.pack(side="left", padx=6)

    btn_login = tk.Button(
        botones_frame, text="Probar acceso", command=probar_login,
        bg=T.STAT_2, fg=T.WHITE, font=F_BODY_B, relief="flat", padx=14, pady=8, cursor="hand2",
        activebackground="#7c3aed", activeforeground=T.WHITE,
    )
    btn_login.pack(side="left", padx=6)

    btn_refrescar = tk.Button(
        botones_frame, text="Refrescar tabla", command=refrescar_tabla,
        bg=T.STAT_1, fg=T.WHITE, font=F_BODY_B, relief="flat", padx=14, pady=8, cursor="hand2",
        activebackground="#0284c7", activeforeground=T.WHITE,
    )
    btn_refrescar.pack(side="left", padx=6)

    tabla_frame = tk.Frame(main_frame, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
    tabla_frame.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
    tk.Frame(tabla_frame, bg=T.POS_HEADER, height=3).pack(fill="x")
    tk.Label(tabla_frame, text="Usuarios registrados", font=F_HEAD, bg=T.BG_CARD, fg=T.TEXT).pack(anchor="w", padx=14, pady=(10, 6))
    tabla_wrap = tk.Frame(tabla_frame, bg=T.BG_CARD)
    tabla_wrap.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    columnas = ("ID", "Usuario", "Rol", "Estado", "Último Acceso", "Fecha Registro")
    tabla = ttk.Treeview(tabla_wrap, columns=columnas, show="headings", height=14)
    
    # Configurar columnas
    anchos_columnas = {"ID": 60, "Usuario": 150, "Rol": 120, "Estado": 100, "Último Acceso": 150, "Fecha Registro": 150}
    
    for col in columnas:
        tabla.heading(col, text=col)
        tabla.column(col, width=anchos_columnas.get(col, 120), anchor="center", stretch=True, minwidth=50)
    
    scrollbar = ttk.Scrollbar(tabla_wrap, orient="vertical", command=tabla.yview)
    tabla.configure(yscrollcommand=scrollbar.set)

    tabla.pack(side="left", fill="both", expand=True, padx=(0, 4), pady=4)
    scrollbar.pack(side="right", fill="y", pady=4)
    
    # Vincular evento de selección
    tabla.bind("<<TreeviewSelect>>", seleccionar_usuario)

    info_frame = tk.Frame(tabla_frame, bg=T.BG_CARD)
    info_frame.pack(fill="x", padx=14, pady=(0, 10))

    tk.Label(
        info_frame,
        text="Seleccione una fila para cargar los datos en el formulario superior.",
        font=F_SMALL,
        bg=T.BG_CARD,
        fg=T.TEXT_MUTED,
    ).pack(anchor="w")

    footer = tk.Frame(cuerpo, bg=T.FOOTER, height=48)
    footer.pack(fill=tk.X)
    footer.pack_propagate(False)

    usuarios_count = len(obtener_usuarios())
    tk.Label(
        footer,
        text=f"VmPOS v3.1.0 · {usuarios_count} usuario(s) · Puerto Colombia",
        font=F_SMALL,
        bg=T.FOOTER,
        fg=T.HEADER_TEXT_DIM,
    ).pack(expand=True, pady=14)

    # Cargar datos iniciales en la tabla
    actualizar_tabla()

    modulo_scroll_finalizar(cuerpo)
    
    # Focus inicial en el campo usuario
    entradas['Usuario'].focus()
    
    # Vincular teclas de acceso rápido
    ventana_usuarios.bind('<F5>', lambda e: refrescar_tabla())
    ventana_usuarios.bind('<Escape>', lambda e: limpiar_campos())
    ventana_usuarios.bind('<Control-s>', lambda e: guardar_usuario())
    
    if parent is None:
        ventana_usuarios.mainloop()

if __name__ == "__main__":
    iniciar_usuarios()