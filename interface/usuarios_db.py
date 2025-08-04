# -*- coding: utf-8 -*-
import sqlite3
import os
import hashlib
from datetime import datetime

# 📦 Ruta de la base de datos
base_dir = os.path.dirname(os.path.abspath(__file__))
ruta_db = os.path.join(base_dir, '..', 'database', 'ventas.db')

# Asegurar que el directorio de la base de datos existe
os.makedirs(os.path.join(base_dir, 'database'), exist_ok=True)

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

            # Inicializar permisos para el nuevo usuario
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

def verificar_credenciales(usuario, contrasena_ingresada):
    """
    Verifica las credenciales de un usuario.
    Retorna los datos del usuario si las credenciales son correctas,
    de lo contrario retorna None.
    """
    conn = obtener_conexion()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM usuarios WHERE usuario = ?", (usuario,))
            usuario_db = cursor.fetchone()

            if usuario_db:
                # Comprobar primero con la contraseña hasheada
                contrasena_hasheada_ingresada = hash_password(contrasena_ingresada)
                if contrasena_hasheada_ingresada == usuario_db['contrasena']:
                    return dict(usuario_db) # Login exitoso con contraseña hasheada
                
                # Solución temporal: comprobar con contraseña de texto plano
                if contrasena_ingresada == usuario_db['contrasena']:
                    return dict(usuario_db) # Login exitoso con contraseña en texto plano

            return None # Credenciales incorrectas
        except sqlite3.Error as e:
            print(f"Error al verificar credenciales: {e}")
            return None
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

def inicializar_permisos_usuario(usuario_id):
    """Inicializa los permisos de un nuevo usuario con acceso total a todos los módulos."""
    conn = obtener_conexion()
    if conn:
        cursor = conn.cursor()
        try:
            for modulo in MODULOS_DISPONIBLES:
                cursor.execute(
                    "INSERT INTO permisos (usuario_id, modulo, permiso) VALUES (?, ?, ?)",
                    (usuario_id, modulo, 1) # 1 = Acceso Total
                )
            conn.commit()
            print(f"Permisos iniciales creados para el usuario ID {usuario_id}.")
            return True
        except sqlite3.Error as e:
            print(f"Error al inicializar permisos: {e}")
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

# Llamar a la función para crear las tablas al importar el módulo
crear_tablas_iniciales()
