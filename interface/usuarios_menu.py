# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import os
import sqlite3
import hashlib

# Importar funciones de la base de datos de usuarios
# Asegúrate de que usuarios_db.py esté en la misma carpeta o en el path correcto.
from usuarios_db import (
    crear_tablas_iniciales, insertar_usuario, obtener_usuarios,
    actualizar_usuario_db, eliminar_usuario_db,
    obtener_permisos_por_usuario, MODULOS_DISPONIBLES, hash_password,
    verificar_credenciales
)

# 🌐 Variables globales para los widgets de la interfaz
entradas = {}
tabla = None
ventana_usuarios = None
rol_var = None
estado_var = None
id_usuario_seleccionado = None

# --- Iniciar tablas de la base de datos al arrancar el script ---
crear_tablas_iniciales()

def cargar_datos_ejemplo():
    """Carga datos de ejemplo si la base de datos está vacía."""
    conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'database', 'ventas.db'))
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    count = cursor.fetchone()[0]
    conn.close()

    if count == 0:
        print("La base de datos de usuarios está vacía. Cargando datos de ejemplo...")
        insertar_usuario("admin", "admin123", "Administrador", "Activo")
        insertar_usuario("vendedor", "pass123", "Vendedor", "Activo")
        insertar_usuario("gerente", "manager", "Gerente", "Activo")
        print("Datos de ejemplo cargados.")
        return True
    else:
        print(f"Se encontraron {count} usuarios en la base de datos. No se cargan datos de ejemplo.")
    return False

def actualizar_tabla():
    """
    Borra todos los elementos de la tabla y los vuelve a insertar
    con los datos actualizados de la base de datos.
    """
    global tabla
    
    # Limpiar tabla
    for i in tabla.get_children():
        tabla.delete(i)

    # Obtener usuarios de la base de datos
    usuarios = obtener_usuarios()
    print(f"Recibidos {len(usuarios)} usuarios de la base de datos para mostrar en la tabla.")

    # Insertar los nuevos datos
    for user in usuarios:
        # Convertir la fila de la base de datos a una tupla para la tabla
        valores = (user['id'], user['usuario'], user['rol'], user['estado'], user['ultimo_acceso'], user['fecha_registro'])
        tabla.insert("", "end", values=valores)
    print("Tabla actualizada.")

def seleccionar_usuario(event):
    """
    Obtiene los datos del usuario seleccionado y los carga en los campos de entrada.
    """
    global id_usuario_seleccionado
    global entradas, rol_var, estado_var

    item_seleccionado = tabla.focus()
    if item_seleccionado:
        # Obtener los valores de la fila seleccionada
        valores = tabla.item(item_seleccionado, 'values')
        
        # Guardar el ID del usuario seleccionado
        id_usuario_seleccionado = valores[0]
        
        # Cargar los valores en los campos de entrada
        entradas['Usuario'].delete(0, tk.END)
        entradas['Usuario'].insert(0, valores[1])
        
        # El campo de contraseña no se carga por seguridad
        entradas['Password'].delete(0, tk.END)
        
        rol_var.set(valores[2])
        estado_var.set(valores[3])

def guardar_usuario():
    """
    Guarda o actualiza un usuario en la base de datos.
    """
    global id_usuario_seleccionado
    
    usuario = entradas['Usuario'].get()
    password = entradas['Password'].get()
    rol = rol_var.get()
    estado = estado_var.get()
    
    if not usuario or not rol or not estado:
        messagebox.showerror("Error", "Los campos Usuario, Rol y Estado son obligatorios.")
        return
    
    if not id_usuario_seleccionado and not password:
        messagebox.showerror("Error", "La contraseña es obligatoria para un nuevo usuario.")
        return
        
    try:
        if id_usuario_seleccionado:
            # Actualizar usuario existente
            actualizar_usuario_db(id_usuario_seleccionado, usuario, rol, estado)
            messagebox.showinfo("Éxito", "Usuario actualizado correctamente.")
        else:
            # Crear nuevo usuario
            if insertar_usuario(usuario, password, rol, estado):
                messagebox.showinfo("Éxito", "Usuario creado correctamente.")
            else:
                messagebox.showerror("Error", "El usuario ya existe.")
        
        limpiar_campos()
        actualizar_tabla()
    except Exception as e:
        messagebox.showerror("Error de base de datos", f"Ocurrió un error al guardar el usuario: {e}")

def eliminar_usuario():
    """
    Elimina el usuario seleccionado de la base de datos.
    """
    global id_usuario_seleccionado
    if id_usuario_seleccionado:
        respuesta = messagebox.askyesno("Confirmar", f"¿Estás seguro de que quieres eliminar el usuario con ID {id_usuario_seleccionado}?")
        if respuesta:
            try:
                eliminar_usuario_db(id_usuario_seleccionado)
                messagebox.showinfo("Éxito", "Usuario eliminado correctamente.")
                limpiar_campos()
                actualizar_tabla()
            except Exception as e:
                messagebox.showerror("Error de base de datos", f"Ocurrió un error al eliminar el usuario: {e}")
    else:
        messagebox.showwarning("Advertencia", "Por favor, selecciona un usuario de la tabla para eliminar.")

def limpiar_campos():
    """
    Limpia los campos de entrada y restablece la selección.
    """
    global id_usuario_seleccionado
    
    for campo in ["Usuario", "Password"]:
        if campo in entradas:
            entradas[campo].delete(0, tk.END)
    
    if rol_var:
        rol_var.set("Seleccionar")
    if estado_var:
        estado_var.set("Seleccionar")

    id_usuario_seleccionado = None
    if tabla:
        tabla.selection_remove(tabla.selection())
        
def probar_login():
    """Función para probar la nueva verificación de credenciales."""
    usuario = entradas['Usuario'].get()
    contrasena = entradas['Password'].get()

    if not usuario or not contrasena:
        messagebox.showerror("Error", "Por favor, introduce un usuario y una contraseña.")
        return
        
    usuario_verificado = verificar_credenciales(usuario, contrasena)

    if usuario_verificado:
        messagebox.showinfo("Login Exitoso", f"Bienvenido, {usuario_verificado['usuario']}!")
    else:
        messagebox.showerror("Login Fallido", "Credenciales incorrectas.")


def iniciar_usuarios():
    global tabla, entradas, ventana_usuarios, rol_var, estado_var
    
    print("Iniciando la ventana de gestión de usuarios...")
    ventana_usuarios = tk.Tk()
    ventana_usuarios.title("👥 Gestión de Usuarios - VmPOS")
    ventana_usuarios.geometry("1200x750")
    ventana_usuarios.resizable(False, False)
    ventana_usuarios.configure(bg="#FFE4F1")

    # Centrar ventana
    ventana_usuarios.update_idletasks()
    x = (ventana_usuarios.winfo_screenwidth() // 2) - 600
    y = (ventana_usuarios.winfo_screenheight() // 2) - 375
    ventana_usuarios.geometry(f"1200x750+{x}+{y}")
    
    # Cargar datos de ejemplo si la base de datos está vacía
    cargar_datos_ejemplo()

    # Estilo Femenino
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('Feminine.TLabel', background='#FFE4F1', foreground='#C71585', font=('Segoe UI', 10))
    style.configure('Header.TLabel', background='#FF1493', foreground='white', font=('Segoe UI', 16, 'bold'))
    style.configure('Feminine.TButton', background='#FF69B4', foreground='white', font=('Segoe UI', 10, 'bold'), relief="flat")
    
    # Estilo para la tabla
    style.configure("Treeview",
                    background="#FADDEE",
                    foreground="#333",
                    rowheight=25,
                    fieldbackground="#FADDEE")
    style.map('Treeview', background=[('selected', '#fd79a8')], foreground=[('selected', 'white')])
    style.configure("Treeview.Heading",
                    font=("Segoe UI", 10, "bold"),
                    background="#e84393",
                    foreground="white",
                    relief="flat")
    style.map("Treeview.Heading", background=[('active', '#e84393')])

    # 🌸 Header principal
    header_frame = tk.Frame(ventana_usuarios, bg="#FF1493", height=80)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)

    tk.Label(header_frame, text="👥 Gestión de Usuarios del Sistema",
             font=("Segoe UI", 20, "bold"), bg="#FF1493", fg="white").pack(pady=15)

    # Contenedor principal para el formulario y la tabla
    main_frame = tk.Frame(ventana_usuarios, bg="#FFE4F1")
    main_frame.pack(fill="both", expand=True, padx=20, pady=10)

    # Formulario para nuevos usuarios y edición
    form_frame = tk.LabelFrame(main_frame, text="✨ Nuevo/Editar Usuario", font=("Segoe UI", 12, "bold"),
                               bg="#FFDDEE", fg="#C71585", padx=10, pady=10, relief="flat")
    form_frame.pack(fill="x", padx=10, pady=10)
    
    campos = ["Usuario", "Password", "Rol", "Estado"]
    roles = ["Administrador", "Gerente", "Vendedor"]
    estados = ["Activo", "Inactivo"]
    
    # Variables de control para Comboboxes
    rol_var = tk.StringVar(value="Seleccionar")
    estado_var = tk.StringVar(value="Seleccionar")
    
    # Crear entradas del formulario
    row_count = 0
    for i, campo in enumerate(campos):
        tk.Label(form_frame, text=campo + ":", font=("Segoe UI", 10), bg="#FFDDEE", fg="#C71585").grid(row=row_count, column=0, padx=5, pady=5, sticky="w")
        
        if campo == "Rol":
            entrada = ttk.Combobox(form_frame, textvariable=rol_var, values=roles, state="readonly", width=30)
            entrada.grid(row=row_count, column=1, padx=5, pady=5, sticky="w")
        elif campo == "Estado":
            entrada = ttk.Combobox(form_frame, textvariable=estado_var, values=estados, state="readonly", width=30)
            entrada.grid(row=row_count, column=1, padx=5, pady=5, sticky="w")
        else:
            # Ahora la contraseña se oculta
            show_char = '*' if campo == 'Password' else None
            entrada = tk.Entry(form_frame, font=("Segoe UI", 10), width=30, bg="#FFFFFF", fg="#C71585", bd=1, relief="solid", show=show_char)
            entrada.grid(row=row_count, column=1, padx=5, pady=5, sticky="w")
        entradas[campo] = entrada
        row_count += 1
    
    # Botones de acción
    botones_frame = tk.Frame(form_frame, bg="#FFDDEE")
    botones_frame.grid(row=row_count, column=0, columnspan=2, pady=10)
    
    btn_guardar = tk.Button(botones_frame, text="💾 Guardar", command=guardar_usuario, bg="#FF69B4", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=10)
    btn_guardar.pack(side="left", padx=5)
    
    btn_eliminar = tk.Button(botones_frame, text="🗑️ Eliminar", command=eliminar_usuario, bg="#ff4d4d", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=10)
    btn_eliminar.pack(side="left", padx=5)
    
    btn_limpiar = tk.Button(botones_frame, text="🧹 Limpiar", command=limpiar_campos, bg="#3399ff", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=10)
    btn_limpiar.pack(side="left", padx=5)

    # Nuevo botón para probar el login
    btn_login = tk.Button(botones_frame, text="🔑 Verificar Login", command=probar_login, bg="#8B008B", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=10)
    btn_login.pack(side="left", padx=5)


    # Tabla de usuarios
    tabla_frame = tk.LabelFrame(main_frame, text="📋 Lista de Usuarios", font=("Segoe UI", 12, "bold"),
                                bg="#FFE4F1", fg="#C71585", padx=10, pady=10, relief="flat")
    tabla_frame.pack(fill="both", expand=True, padx=10, pady=10)

    columnas = ("ID", "Usuario", "Rol", "Estado", "Último Acceso", "Registro")
    tabla = ttk.Treeview(tabla_frame, columns=columnas, show="headings")
    
    for col in columnas:
        tabla.heading(col, text=col)
        tabla.column(col, width=120, anchor="center")
    
    tabla.pack(fill="both", expand=True, padx=20, pady=10)
    tabla.bind("<<TreeviewSelect>>", seleccionar_usuario)

    actualizar_tabla()
    
    # 📊 Footer con información del sistema
    footer = tk.Frame(ventana_usuarios, bg="#e84393", height=50)
    footer.pack(fill="x", side="bottom")
    footer.pack_propagate(False)

    footer_left = tk.Frame(footer, bg="#e84393")
    footer_left.pack(side="left", padx=20, pady=10)

    footer_right = tk.Frame(footer, bg="#e84393")
    footer_right.pack(side="right", padx=20, pady=10)

    tk.Label(footer_left, text="📍 Puerto Colombia • 📞 +573215545788",
             font=("Segoe UI", 10), bg="#e84393", fg="white").pack()

    tk.Label(footer_right, text="✨ VmPOS v3.1.0 • Sistema Activo 💖",
             font=("Segoe UI", 10), bg="#e84393", fg="#ffd3e8").pack()

    ventana_usuarios.mainloop()

if __name__ == "__main__":
    iniciar_usuarios()
