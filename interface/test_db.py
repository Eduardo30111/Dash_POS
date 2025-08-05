#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para crear usuarios iniciales en VmPOS
Ejecuta este script para configurar los usuarios de prueba
"""

import os
import sys

# Agregar el directorio actual al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from usuarios_db import (
    crear_tablas_iniciales, 
    insertar_usuario, 
    obtener_usuarios,
    obtener_conexion
)
import sqlite3

def limpiar_usuarios_existentes():
    """Elimina todos los usuarios existentes para empezar limpio"""
    conn = obtener_conexion()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM permisos")
            cursor.execute("DELETE FROM usuarios")
            conn.commit()
            print("✅ Usuarios existentes eliminados")
        except sqlite3.Error as e:
            print(f"❌ Error al limpiar usuarios: {e}")
        finally:
            conn.close()

def crear_usuarios_sistema():
    """Crea los usuarios del sistema"""
    print("🚀 Iniciando creación de usuarios del sistema VmPOS...")
    
    # Crear las tablas si no existen
    print("📊 Creando tablas de base de datos...")
    crear_tablas_iniciales()
    
    # Limpiar usuarios existentes (opcional)
    respuesta = input("❓ ¿Deseas eliminar usuarios existentes? (s/N): ").lower()
    if respuesta in ['s', 'si', 'sí', 'y', 'yes']:
        limpiar_usuarios_existentes()
    
    # Definir usuarios a crear
    usuarios_crear = [
        {
            'usuario': 'eduardo',
            'contrasena': '2121',
            'rol': 'Administrador',
            'estado': 'Activo',
            'descripcion': 'Usuario administrador con acceso completo'
        },
        {
            'usuario': 'andres',
            'contrasena': '2180',
            'rol': 'Vendedor',
            'estado': 'Activo',
            'descripcion': 'Usuario vendedor con acceso limitado'
        }
    ]
    
    print("\n👥 Creando usuarios...")
    
    for usuario_data in usuarios_crear:
        print(f"\n📝 Creando usuario: {usuario_data['usuario']}")
        print(f"   - Rol: {usuario_data['rol']}")
        print(f"   - Descripción: {usuario_data['descripcion']}")
        
        exito = insertar_usuario(
            usuario_data['usuario'],
            usuario_data['contrasena'],
            usuario_data['rol'],
            usuario_data['estado']
        )
        
        if exito:
            print(f"   ✅ Usuario '{usuario_data['usuario']}' creado exitosamente")
        else:
            print(f"   ❌ Error al crear usuario '{usuario_data['usuario']}'")
    
    print("\n📋 Listado de usuarios creados:")
    usuarios = obtener_usuarios()
    
    if usuarios:
        print("\n" + "="*80)
        print(f"{'ID':<5} {'USUARIO':<15} {'ROL':<15} {'ESTADO':<10} {'FECHA REGISTRO':<20}")
        print("="*80)
        
        for usuario in usuarios:
            print(f"{usuario['id']:<5} {usuario['usuario']:<15} {usuario['rol']:<15} {usuario['estado']:<10} {usuario['fecha_registro'] or 'N/A':<20}")
        
        print("="*80)
        print(f"\n✅ Total de usuarios creados: {len(usuarios)}")
    else:
        print("❌ No se encontraron usuarios en la base de datos")
    
    print("\n🎯 INFORMACIÓN DE ACCESO:")
    print("=" * 50)
    print("👑 ADMINISTRADOR:")
    print("   Usuario: eduardo")
    print("   Contraseña: 2121")
    print("   Permisos: Acceso completo a todos los módulos")
    print()
    print("🛍️ VENDEDOR:")
    print("   Usuario: andres")
    print("   Contraseña: 2180")
    print("   Permisos: Ventas, Inventario, Clientes, Reportes")
    print("=" * 50)
    
    print("\n🚀 ¡Sistema listo! Puedes ejecutar inicio_sesion.py para probar el login")

def verificar_base_datos():
    """Verifica el estado actual de la base de datos"""
    print("🔍 Verificando estado de la base de datos...")
    
    usuarios = obtener_usuarios()
    if usuarios:
        print(f"📊 Se encontraron {len(usuarios)} usuarios:")
        for usuario in usuarios:
            print(f"   - {usuario['usuario']} ({usuario['rol']}) - {usuario['estado']}")
    else:
        print("📭 No hay usuarios en la base de datos")
    
    return len(usuarios) if usuarios else 0

def menu_principal():
    """Menú principal del script"""
    while True:
        print("\n" + "="*60)
        print("🌸 VMPOS - GESTIÓN DE USUARIOS")
        print("="*60)
        print("1. 👥 Crear usuarios del sistema")
        print("2. 🔍 Verificar usuarios existentes")
        print("3. 🧹 Limpiar todos los usuarios")
        print("4. ❌ Salir")
        print("="*60)
        
        opcion = input("Selecciona una opción (1-4): ").strip()
        
        if opcion == "1":
            crear_usuarios_sistema()
        elif opcion == "2":
            verificar_base_datos()
        elif opcion == "3":
            confirmacion = input("⚠️ ¿Estás seguro de eliminar TODOS los usuarios? (s/N): ").lower()
            if confirmacion in ['s', 'si', 'sí', 'y', 'yes']:
                limpiar_usuarios_existentes()
                print("✅ Todos los usuarios han sido eliminados")
            else:
                print("❌ Operación cancelada")
        elif opcion == "4":
            print("👋 ¡Hasta luego!")
            break
        else:
            print("❌ Opción no válida")

if __name__ == "__main__":
    try:
        menu_principal()
    except KeyboardInterrupt:
        print("\n\n👋 Proceso interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        print("🔧 Por favor, verifica la configuración de la base de datos")