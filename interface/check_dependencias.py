#!/usr/bin/env python37
"""
Script para verificar todas las dependencias de VmPOS
"""

import sys

def verificar_dependencias():
    """Verifica que todas las dependencias estén instaladas"""
    
    dependencias = {
        'tkinter': 'Interfaz gráfica',
        'PIL': 'Procesamiento de imágenes (Pillow)',
        'sqlite3': 'Base de datos',
        'pyttsx3': 'Síntesis de voz',
        'reportlab': 'Generación de PDFs',
        'matplotlib': 'Gráficos y reportes',
        'pandas': 'Análisis de datos',
        'openpyxl': 'Archivos Excel'
    }
    
    print("🔍 VERIFICANDO DEPENDENCIAS DE VmPOS")
    print("=" * 50)
    
    faltantes = []
    
    for modulo, descripcion in dependencias.items():
        try:
            __import__(modulo)
            print(f"✅ {modulo:<15} - {descripcion}")
        except ImportError:
            print(f"❌ {modulo:<15} - {descripcion} (FALTANTE)")
            faltantes.append(modulo)
    
    print("=" * 50)
    
    if faltantes:
        print(f"\n❌ FALTAN {len(faltantes)} DEPENDENCIAS:")
        for modulo in faltantes:
            print(f"   • {modulo}")
        
        print("\n📥 PARA INSTALAR:")
        print("pip install " + " ".join(faltantes))
        print("\nO ejecuta:")
        print("pip install -r requirements.txt")
        
        return False
    else:
        print("\n✅ TODAS LAS DEPENDENCIAS ESTÁN INSTALADAS")
        print("🚀 VmPOS está listo para compilar!")
        return True

def verificar_archivos():
    """Verifica que todos los archivos necesarios existan"""
    import os
    
    archivos_necesarios = [
        'main.py',
        'interface/inicio_sesion.py',
        'interface/pantalla_carga.py', 
        'interface/generador_codigo_barras.py',
        'database/crear_db.py',
        # Agrega aquí otros archivos que tengas en tu proyecto
        'interface/menu_inicio.py',  # Si existe
        'interface/ventas_menu.py',  # Si existe
        'interface/gastos_menu.py',  # Si existe
        'interface/configuracion_menu.py',  # Si existe
        'interface/usuarios_menu.py',  # Si existe
        'interface/clientes_menu.py',  # Si existe
    ]
    
    print("\n📁 VERIFICANDO ARCHIVOS DEL PROYECTO")
    print("=" * 50)
    
    faltantes = []
    presentes = []
    
    for archivo in archivos_necesarios:
        if os.path.exists(archivo):
            print(f"✅ {archivo}")
            presentes.append(archivo)
        else:
            print(f"⚠️  {archivo} (OPCIONAL - NO ENCONTRADO)")
            # Solo marcar como faltante si es crítico
            if 'inicio_sesion.py' in archivo or 'main.py' in archivo:
                faltantes.append(archivo)
    
    # Verificar estructura de directorios
    directorios = ['interface', 'database', 'assets']
    print(f"\n📂 VERIFICANDO ESTRUCTURA DE DIRECTORIOS")
    print("=" * 50)
    
    for directorio in directorios:
        if os.path.exists(directorio):
            print(f"✅ {directorio}/")
        else:
            print(f"⚠️  {directorio}/ (se creará automáticamente)")
    
    if faltantes:
        print(f"\n❌ ARCHIVOS CRÍTICOS FALTANTES:")
        for archivo in faltantes:
            print(f"   • {archivo}")
        return False
    else:
        print(f"\n✅ ARCHIVOS CRÍTICOS PRESENTES ({len(presentes)} archivos encontrados)")
        return True

if __name__ == "__main__":
    print("🛠️  VERIFICADOR DE SISTEMA VmPOS")
    print("=" * 50)
    
    deps_ok = verificar_dependencias()
    files_ok = verificar_archivos()
    
    print("\n" + "=" * 50)
    if deps_ok and files_ok:
        print("🎉 ¡SISTEMA LISTO PARA COMPILAR!")
        print("\nEjecuta:")
        print("  • build.bat (Windows)")
        print("  • auto-py-to-exe")
        print("  • pyinstaller VmPOS.spec")
    else:
        print("⚠️  CORRIGE LOS ERRORES ANTES DE COMPILAR")
    
    input("\nPresiona Enter para salir...")