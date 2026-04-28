#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Archivo: usuarios_db.py
Módulo para la gestión de la base de datos de usuarios del sistema VmPOS.
"""

import sqlite3
import hashlib
import os
from datetime import datetime

from paths import usuarios_db_path

# Módulos disponibles en el sistema
MODULOS_DISPONIBLES = [
    "ventas",
    "inventario", 
    "usuarios",
    "reportes",
    "configuracion"
]

def hash_password(password):
    """
    Genera un hash SHA-256 de la contraseña.
    """
    return hashlib.sha256(password.encode()).hexdigest()

def crear_tablas_iniciales():
    """
    Crea las tablas necesarias en la base de datos si no existen.
    """
    try:
        conn = sqlite3.connect(usuarios_db_path())
        cursor = conn.cursor()
        
        # Crear tabla de usuarios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                rol TEXT NOT NULL,
                estado TEXT NOT NULL DEFAULT 'Activo',
                ultimo_acceso DATETIME,
                fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
                fecha_modificacion DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Crear tabla de permisos (para funcionalidades futuras)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS permisos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER,
                modulo TEXT NOT NULL,
                permiso TEXT NOT NULL,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Tablas de usuarios creadas/verificadas correctamente.")
        return True
        
    except Exception as e:
        print(f"❌ Error al crear tablas: {e}")
        return False

def insertar_usuario(usuario, password, rol, estado="Activo"):
    """
    Inserta un nuevo usuario en la base de datos.
    
    Args:
        usuario (str): Nombre de usuario
        password (str): Contraseña en texto plano
        rol (str): Rol del usuario (Administrador, Gerente, Vendedor)
        estado (str): Estado del usuario (Activo, Inactivo)
    
    Returns:
        bool: True si se insertó correctamente, False si ya existe
    """
    try:
        conn = sqlite3.connect(usuarios_db_path())
        cursor = conn.cursor()
        
        # Verificar si el usuario ya existe
        cursor.execute("SELECT id FROM usuarios WHERE usuario = ?", (usuario,))
        if cursor.fetchone():
            print(f"⚠️ El usuario '{usuario}' ya existe.")
            conn.close()
            return False
        
        # Insertar nuevo usuario
        password_hash = hash_password(password)
        cursor.execute('''
            INSERT INTO usuarios (usuario, password, rol, estado, fecha_registro, fecha_modificacion)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (usuario, password_hash, rol, estado, datetime.now(), datetime.now()))
        
        conn.commit()
        conn.close()
        print(f"✅ Usuario '{usuario}' creado correctamente.")
        return True
        
    except Exception as e:
        print(f"❌ Error al insertar usuario: {e}")
        return False

def obtener_usuarios():
    """
    Obtiene todos los usuarios de la base de datos.
    
    Returns:
        list: Lista de diccionarios con información de usuarios
    """
    try:
        conn = sqlite3.connect(usuarios_db_path())
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, usuario, rol, estado, ultimo_acceso, fecha_registro
            FROM usuarios
            ORDER BY fecha_registro DESC
        ''')
        
        usuarios = []
        for row in cursor.fetchall():
            usuarios.append({
                'id': row[0],
                'usuario': row[1],
                'rol': row[2],
                'estado': row[3],
                'ultimo_acceso': row[4] if row[4] else "Nunca",
                'fecha_registro': row[5]
            })
        
        conn.close()
        return usuarios
        
    except Exception as e:
        print(f"❌ Error al obtener usuarios: {e}")
        return []

def actualizar_usuario_db(id_usuario, usuario=None, rol=None, estado=None, password=None):
    """
    Actualiza la información de un usuario existente.
    
    Args:
        id_usuario (int): ID del usuario a actualizar
        usuario (str, optional): Nuevo nombre de usuario
        rol (str, optional): Nuevo rol
        estado (str, optional): Nuevo estado
        password (str, optional): Nueva contraseña en texto plano
    
    Returns:
        bool: True si se actualizó correctamente, False en caso contrario
    """
    try:
        conn = sqlite3.connect(usuarios_db_path())
        cursor = conn.cursor()
        
        # Construir la consulta dinámicamente
        campos_actualizar = []
        valores = []
        
        if usuario:
            campos_actualizar.append("usuario = ?")
            valores.append(usuario)
        
        if rol:
            campos_actualizar.append("rol = ?")
            valores.append(rol)
        
        if estado:
            campos_actualizar.append("estado = ?")
            valores.append(estado)
        
        if password:
            campos_actualizar.append("password = ?")
            valores.append(hash_password(password))
        
        # Siempre actualizar fecha de modificación
        campos_actualizar.append("fecha_modificacion = ?")
        valores.append(datetime.now())
        
        # Agregar ID al final para la condición WHERE
        valores.append(id_usuario)
        
        if campos_actualizar:
            consulta = f"UPDATE usuarios SET {', '.join(campos_actualizar)} WHERE id = ?"
            cursor.execute(consulta, valores)
            conn.commit()
        
        conn.close()
        print(f"✅ Usuario con ID {id_usuario} actualizado correctamente.")
        return True
        
    except Exception as e:
        print(f"❌ Error al actualizar usuario: {e}")
        return False

def eliminar_usuario_db(id_usuario):
    """
    Elimina un usuario de la base de datos.
    
    Args:
        id_usuario (int): ID del usuario a eliminar
    
    Returns:
        bool: True si se eliminó correctamente, False en caso contrario
    """
    try:
        conn = sqlite3.connect(usuarios_db_path())
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM usuarios WHERE id = ?", (id_usuario,))
        conn.commit()
        conn.close()
        
        print(f"✅ Usuario con ID {id_usuario} eliminado correctamente.")
        return True
        
    except Exception as e:
        print(f"❌ Error al eliminar usuario: {e}")
        return False

def obtener_usuario_por_credenciales(usuario, password):
    """
    Verifica las credenciales de un usuario y retorna su información.
    
    Args:
        usuario (str): Nombre de usuario
        password (str): Contraseña en texto plano
    
    Returns:
        dict or None: Información del usuario si las credenciales son correctas, None en caso contrario
    """
    try:
        conn = sqlite3.connect(usuarios_db_path())
        cursor = conn.cursor()
        
        password_hash = hash_password(password)
        cursor.execute('''
            SELECT id, usuario, rol, estado, ultimo_acceso, fecha_registro
            FROM usuarios
            WHERE usuario = ? AND password = ? AND estado = 'Activo'
        ''', (usuario, password_hash))
        
        resultado = cursor.fetchone()
        
        if resultado:
            # Actualizar último acceso
            cursor.execute('''
                UPDATE usuarios SET ultimo_acceso = ?
                WHERE id = ?
            ''', (datetime.now(), resultado[0]))
            conn.commit()
            
            usuario_info = {
                'id': resultado[0],
                'usuario': resultado[1],
                'rol': resultado[2],
                'estado': resultado[3],
                'ultimo_acceso': resultado[4],
                'fecha_registro': resultado[5],
                'permisos': resultado[2].lower()  # Para compatibilidad con el sistema existente
            }
            
            conn.close()
            return usuario_info
        
        conn.close()
        return None
        
    except Exception as e:
        print(f"❌ Error al verificar credenciales: {e}")
        return None

def obtener_permisos_por_usuario(usuario_id):
    """
    Obtiene los permisos específicos de un usuario.
    
    Args:
        usuario_id (int): ID del usuario
    
    Returns:
        list: Lista de permisos del usuario
    """
    try:
        conn = sqlite3.connect(usuarios_db_path())
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT modulo, permiso
            FROM permisos
            WHERE usuario_id = ?
        ''', (usuario_id,))
        
        permisos = cursor.fetchall()
        conn.close()
        
        return permisos
        
    except Exception as e:
        print(f"❌ Error al obtener permisos: {e}")
        return []

def asegurar_cuenta_administrador(usuario="admin", password="admin123"):
    """
    Crea o restablece el usuario indicado como Administrador con la contraseña dada
    (misma lógica que el login: hash SHA-256). Útil si olvidaste la clave o la BD
    quedó inconsistente.
    """
    crear_tablas_iniciales()
    conn = sqlite3.connect(usuarios_db_path())
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM usuarios WHERE usuario = ?", (usuario,))
        row = cursor.fetchone()
    finally:
        conn.close()
    if row:
        actualizar_usuario_db(row[0], password=password, rol="Administrador", estado="Activo")
        return True
    return insertar_usuario(usuario, password, "Administrador", "Activo")


def inicializar_admin_default():
    """
    Crea un usuario administrador por defecto si no existe ningún administrador.
    Además, si no existe el usuario 'admin', lo crea aunque ya haya otro administrador.
    """
    try:
        conn = sqlite3.connect(usuarios_db_path())
        cursor = conn.cursor()
        
        # Verificar si existe algún administrador
        cursor.execute("SELECT id FROM usuarios WHERE rol = 'Administrador'")
        if not cursor.fetchone():
            password_hash = hash_password("admin123")
            cursor.execute('''
                INSERT INTO usuarios (usuario, password, rol, estado, fecha_registro, fecha_modificacion)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ("admin", password_hash, "Administrador", "Activo", datetime.now(), datetime.now()))
            conn.commit()
            print("Usuario administrador por defecto creado: admin / admin123")
        else:
            cursor.execute("SELECT id FROM usuarios WHERE usuario = ?", ("admin",))
            if not cursor.fetchone():
                password_hash = hash_password("admin123")
                cursor.execute('''
                    INSERT INTO usuarios (usuario, password, rol, estado, fecha_registro, fecha_modificacion)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', ("admin", password_hash, "Administrador", "Activo", datetime.now(), datetime.now()))
                conn.commit()
                print("Usuario 'admin' agregado (ya habia otro administrador, pero faltaba 'admin')")
        
        conn.close()
        
    except Exception as e:
        print(f"Error al crear administrador por defecto: {e}")

# Función para migrar usuarios existentes (si los tienes en otro formato)
def migrar_usuarios_existentes():
    """
    Función auxiliar para migrar usuarios desde el sistema de login actual.
    Puedes usar esta función para añadir los usuarios hardcodeados del inicio_sesion.py
    """
    # Usuarios del sistema actual
    usuarios_sistema = [
        {"usuario": "eduardo", "password": "2121", "rol": "Administrador"},
        {"usuario": "andres", "password": "2180", "rol": "Vendedor"}
    ]
    
    for user in usuarios_sistema:
        insertar_usuario(
            user["usuario"],
            user["password"], 
            user["rol"],
            "Activo"
        )

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Base de datos de usuarios VmPOS")
    p.add_argument(
        "--reset-admin",
        action="store_true",
        help="Fuerza usuario admin con contrasena admin123 (recuperar acceso)",
    )
    args = p.parse_args()
    print("Inicializando base de datos de usuarios...")
    crear_tablas_iniciales()
    inicializar_admin_default()
    if args.reset_admin:
        asegurar_cuenta_administrador("admin", "admin123")
        print("Cuenta admin restablecida: usuario admin, contrasena admin123")
    print("Listo:", usuarios_db_path())