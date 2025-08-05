# -*- coding: utf-8 -*-
import sqlite3
import os
import hashlib
from datetime import datetime

# 📦 Ruta de la base de datos
base_dir = os.path.dirname(os.path.abspath(__file__))
ruta_db = os.path.join(base_dir, '..', 'database', 'ventas.db')

# Asegurar que el directorio de la base de datos existe
os.makedirs(os.path.dirname(ruta_db), exist_ok=True)

# --- Constantes y Funciones de Utilidad ---

MODULOS_DISPONIBLES = ["Ventas", "Inventario", "Clientes", "Reportes", "Gastos", "Usuarios", "Configuración"]

def obtener_conexion():
    """Establece y retorna una conexión a la base de datos."""
    try:
        conn = sqlite3.connect(ruta_db)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Error de conexión a la base de datos: {e}")
        return None

def hash_password(password):
    """
    Genera un hash SHA-256 de una contraseña para un almacenamiento seguro.
    """
    return hashlib.sha256(password.encode()).hexdigest()

# --- Funciones de Base de Datos para Usuarios ---

def crear_tablas_iniciales():
    """Crea las tablas de usuarios y permisos si no existen."""
    conn = obtener_conexion()
    if conn:
        cursor = conn.cursor()
        try:
            # Crear tabla de usuarios
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario TEXT NOT NULL UNIQUE,
                    contrasena TEXT NOT NULL,
                    rol TEXT NOT NULL,
                    estado TEXT NOT NULL,
                    ultimo_acceso TEXT,
                    fecha_registro TEXT
                )
            """)

            # Crear tabla de permisos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS permisos (
                    usuario_id INTEGER NOT NULL,
                    modulo TEXT NOT NULL,
                    permiso INTEGER NOT NULL,
                    PRIMARY KEY (usuario_id, modulo),
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
                )
            """)
            conn.commit()
            print("Tablas de usuarios y permisos creadas o ya existentes.")

        except sqlite3.Error as e:
            print(f"Error al crear tablas: {e}")
        finally:
            conn.close()

def insertar_usuario(usuario, contrasena, rol, estado):
    """Inserta un nuevo usuario y sus permisos iniciales en la base de datos."""
    conn = obtener_conexion()
    if conn:
        cursor = conn.cursor()
        contrasena_hashed = hash_password(contrasena)
        fecha_registro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            cursor.execute("""
                INSERT INTO usuarios (usuario, contrasena, rol, estado, fecha_registro)
                VALUES (?, ?, ?, ?, ?)
            """, (usuario, contrasena_hashed, rol, estado, fecha_registro))
            
            usuario_id = cursor.lastrowid
            conn.commit()
            print(f"Usuario '{usuario}' insertado con ID {usuario_id}.")

            # Inicializar permisos para el nuevo usuario según su rol
            if rol == "Administrador":
                inicializar_permisos_administrador(usuario_id)
            elif rol == "Vendedor":
                inicializar_permisos_vendedor(usuario_id)
            else:
                inicializar_permisos_usuario(usuario_id)
            
            return True
        except sqlite3.IntegrityError:
            print(f"Error: El usuario '{usuario}' ya existe.")
            return False
        except sqlite3.Error as e:
            print(f"Error al insertar usuario: {e}")
            return False
        finally:
            conn.close()

def obtener_usuarios():
    """Obtiene todos los usuarios de la base de datos."""
    conn = obtener_conexion()
    usuarios = []
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, usuario, rol, estado, ultimo_acceso, fecha_registro FROM usuarios")
            usuarios = cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener usuarios: {e}")
        finally:
            conn.close()
    return usuarios

def obtener_usuario_por_credenciales(usuario, contrasena_ingresada):
    """
    Función principal para verificar credenciales en el login.
    Retorna los datos del usuario si las credenciales son correctas,
    de lo contrario retorna None.
    """
    conn = obtener_conexion()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM usuarios WHERE usuario = ? AND estado = 'Activo'", (usuario,))
            usuario_db = cursor.fetchone()

            if usuario_db:
                # Verificar contraseña hasheada
                contrasena_hasheada_ingresada = hash_password(contrasena_ingresada)
                if contrasena_hasheada_ingresada == usuario_db['contrasena']:
                    # Actualizar último acceso
                    actualizar_ultimo_acceso(usuario_db['id'])
                    return dict(usuario_db)

            return None # Credenciales incorrectas o usuario inactivo
        except sqlite3.Error as e:
            print(f"Error al verificar credenciales: {e}")
            return None
        finally:
            conn.close()

def actualizar_ultimo_acceso(usuario_id):
    """Actualiza la fecha y hora del último acceso del usuario."""
    conn = obtener_conexion()
    if conn:
        cursor = conn.cursor()
        try:
            ultimo_acceso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("UPDATE usuarios SET ultimo_acceso = ? WHERE id = ?", 
                           (ultimo_acceso, usuario_id))
            conn.commit()
        except sqlite3.Error as e:
            print(f"Error al actualizar último acceso: {e}")
        finally:
            conn.close()

def obtener_permisos_por_usuario(usuario_id):
    """Obtiene los permisos de un usuario como un diccionario."""
    conn = obtener_conexion()
    permisos = {}
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT modulo, permiso FROM permisos WHERE usuario_id = ?", (usuario_id,))
            for modulo, permiso in cursor.fetchall():
                permisos[modulo] = permiso
            return permisos
        except sqlite3.Error as e:
            print(f"Error al obtener permisos: {e}")
            return {}
        finally:
            conn.close()

def inicializar_permisos_administrador(usuario_id):
    """Inicializa los permisos de un administrador con acceso total a todos los módulos."""
    conn = obtener_conexion()
    if conn:
        cursor = conn.cursor()
        try:
            for modulo in MODULOS_DISPONIBLES:
                cursor.execute(
                    "INSERT OR REPLACE INTO permisos (usuario_id, modulo, permiso) VALUES (?, ?, ?)",
                    (usuario_id, modulo, 1) # 1 = Acceso Total
                )
            conn.commit()
            print(f"Permisos de administrador creados para el usuario ID {usuario_id}.")
            return True
        except sqlite3.Error as e:
            print(f"Error al inicializar permisos de administrador: {e}")
            return False
        finally:
            conn.close()

def inicializar_permisos_vendedor(usuario_id):
    """Inicializa los permisos de un vendedor con acceso limitado."""
    conn = obtener_conexion()
    if conn:
        cursor = conn.cursor()
        try:
            # Módulos permitidos para vendedor
            modulos_vendedor = ["Ventas", "Inventario", "Clientes", "Reportes"]
            
            for modulo in MODULOS_DISPONIBLES:
                if modulo in modulos_vendedor:
                    permiso = 1  # Acceso Total
                else:
                    permiso = 0  # Sin Acceso
                
                cursor.execute(
                    "INSERT OR REPLACE INTO permisos (usuario_id, modulo, permiso) VALUES (?, ?, ?)",
                    (usuario_id, modulo, permiso)
                )
            conn.commit()
            print(f"Permisos de vendedor creados para el usuario ID {usuario_id}.")
            return True
        except sqlite3.Error as e:
            print(f"Error al inicializar permisos de vendedor: {e}")
            return False
        finally:
            conn.close()

def inicializar_permisos_usuario(usuario_id):
    """Inicializa los permisos de un usuario básico con acceso limitado."""
    conn = obtener_conexion()
    if conn:
        cursor = conn.cursor()
        try:
            for modulo in MODULOS_DISPONIBLES:
                cursor.execute(
                    "INSERT OR REPLACE INTO permisos (usuario_id, modulo, permiso) VALUES (?, ?, ?)",
                    (usuario_id, modulo, 0) # 0 = Sin Acceso por defecto
                )
            conn.commit()
            print(f"Permisos básicos creados para el usuario ID {usuario_id}.")
            return True
        except sqlite3.Error as e:
            print(f"Error al inicializar permisos básicos: {e}")
            return False
        finally:
            conn.close()

def actualizar_usuario_db(usuario_id, usuario, rol, estado):
    """Actualiza los datos de un usuario en la base de datos."""
    conn = obtener_conexion()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE usuarios
                SET usuario = ?, rol = ?, estado = ?
                WHERE id = ?
            """, (usuario, rol, estado, usuario_id))
            conn.commit()
            print(f"Usuario ID {usuario_id} actualizado.")
            return True
        except sqlite3.Error as e:
            print(f"Error al actualizar usuario: {e}")
            return False
        finally:
            conn.close()

def eliminar_usuario_db(usuario_id):
    """Elimina un usuario de la base de datos."""
    conn = obtener_conexion()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
            conn.commit()
            print(f"Usuario ID {usuario_id} eliminado.")
            return True
        except sqlite3.Error as e:
            print(f"Error al eliminar usuario: {e}")
            return False
        finally:
            conn.close()

def crear_usuarios_iniciales():
    """Crea los usuarios iniciales del sistema si no existen."""
    usuarios_iniciales = [
        ("eduardo", "2121", "Administrador", "Activo"),
        ("andres", "2180", "Vendedor", "Activo")
    ]
    
    for usuario, contrasena, rol, estado in usuarios_iniciales:
        # Verificar si el usuario ya existe
        conn = obtener_conexion()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT id FROM usuarios WHERE usuario = ?", (usuario,))
                if not cursor.fetchone():
                    # El usuario no existe, crearlo
                    insertar_usuario(usuario, contrasena, rol, estado)
                    print(f"Usuario inicial '{usuario}' creado exitosamente.")
                else:
                    print(f"Usuario '{usuario}' ya existe en la base de datos.")
            except sqlite3.Error as e:
                print(f"Error al verificar usuario existente: {e}")
            finally:
                conn.close()

# Esto asegura que las funciones de inicialización solo se ejecuten
# cuando el archivo se corre directamente.
if __name__ == "__main__":
    crear_tablas_iniciales()
    crear_usuarios_iniciales()
