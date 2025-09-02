#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script automatizado para compilar VmPOS con PyInstaller
Ejecuta este script para compilar automáticamente la aplicación
"""

import os
import sys
import subprocess
import shutil
from datetime import datetime

def verificar_dependencias():
    """Verifica que todas las dependencias estén instaladas"""
    dependencias_requeridas = [
        'pyinstaller',
        'auto-py-to-exe',
        'reportlab',
        'matplotlib',
        'pandas',
        'openpyxl',
        'pyttsx3',
        'pillow'
    ]
    
    dependencias_faltantes = []
    
    for dep in dependencias_requeridas:
        try:
            __import__(dep.replace('-', '_'))
            print(f"✅ {dep} - Instalado")
        except ImportError:
            dependencias_faltantes.append(dep)
            print(f"❌ {dep} - NO instalado")
    
    if dependencias_faltantes:
        print(f"\n⚠️ Dependencias faltantes: {', '.join(dependencias_faltantes)}")
        print("Ejecuta: pip install " + " ".join(dependencias_faltantes))
        return False
    
    print("✅ Todas las dependencias están instaladas")
    return True

def limpiar_compilaciones_anteriores():
    """Limpia compilaciones anteriores"""
    directorios_limpiar = ['build', 'dist', '__pycache__']
    archivos_limpiar = ['*.spec']
    
    for directorio in directorios_limpiar:
        if os.path.exists(directorio):
            try:
                shutil.rmtree(directorio)
                print(f"🧹 Directorio {directorio} eliminado")
            except Exception as e:
                print(f"⚠️ No se pudo eliminar {directorio}: {e}")
    
    # Eliminar archivos .spec
    for archivo in os.listdir('.'):
        if archivo.endswith('.spec'):
            try:
                os.remove(archivo)
                print(f"🧹 Archivo {archivo} eliminado")
            except Exception as e:
                print(f"⚠️ No se pudo eliminar {archivo}: {e}")

def compilar_aplicacion():
    """Compila la aplicación usando PyInstaller"""
    
    # Comando PyInstaller optimizado para VmPOS
    comando = [
        'pyinstaller',
        '--onedir',                    # Usar directorio en lugar de archivo único
        '--windowed',                  # Sin ventana de consola
        '--name=VmPOS',               # Nombre del ejecutable
        '--icon=assets/Salome.ico',   # Icono de la aplicación
        '--clean',                    # Limpiar cache
        '--noconfirm',               # No pedir confirmación
        
        # Archivos y carpetas adicionales
        '--add-data=database;database',
        '--add-data=assets;assets',
        '--add-data=interface;interface',
        '--add-data=modules;modules',
        '--add-data=config;config',
        '--add-data=backups;backups',
        '--add-data=reports_pdf;reports_pdf',
        '--add-data=reports_excel;reports_excel',
        
        # Módulos ocultos críticos
        '--hidden-import=pyttsx3',
        '--hidden-import=pyttsx3.drivers',
        '--hidden-import=pyttsx3.drivers.sapi5',
        '--hidden-import=reportlab',
        '--hidden-import=reportlab.lib',
        '--hidden-import=reportlab.lib.pagesizes',
        '--hidden-import=reportlab.platypus',
        '--hidden-import=reportlab.lib.styles',
        '--hidden-import=reportlab.lib.colors',
        '--hidden-import=reportlab.pdfbase',
        '--hidden-import=reportlab.pdfgen',
        '--hidden-import=matplotlib',
        '--hidden-import=matplotlib.pyplot',
        '--hidden-import=matplotlib.backends.backend_tkagg',
        '--hidden-import=matplotlib.dates',
        '--hidden-import=pandas',
        '--hidden-import=openpyxl',
        '--hidden-import=openpyxl.styles',
        '--hidden-import=PIL',
        '--hidden-import=PIL.Image',
        '--hidden-import=PIL.ImageDraw',
        '--hidden-import=sqlite3',
        '--hidden-import=tkinter',
        '--hidden-import=tkinter.ttk',
        '--hidden-import=tkinter.messagebox',
        '--hidden-import=tkinter.filedialog',
        '--hidden-import=escpos',
        '--hidden-import=escpos.printer',
        '--hidden-import=usb.core',
        '--hidden-import=usb.util',
        '--hidden-import=win32print',
        
        # Archivo principal
        'interface/inicio_sesion.py'
    ]
    
    print("🚀 Iniciando compilación con PyInstaller...")
    print(f"📝 Comando: {' '.join(comando)}")
    
    try:
        resultado = subprocess.run(comando, check=True, capture_output=True, text=True)
        print("✅ Compilación exitosa!")
        print(resultado.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("❌ Error durante la compilación:")
        print(e.stderr)
        return False

def post_compilacion():
    """Tareas posteriores a la compilación"""
    dist_dir = "dist/VmPOS"
    
    if not os.path.exists(dist_dir):
        print("❌ Directorio de distribución no encontrado")
        return False
    
    print("🔧 Ejecutando tareas post-compilación...")
    
    # Verificar que las carpetas críticas estén presentes
    carpetas_criticas = ['database', 'assets', 'interface', 'modules']
    
    for carpeta in carpetas_criticas:
        carpeta_path = os.path.join(dist_dir, carpeta)
        if os.path.exists(carpeta_path):
            print(f"✅ {carpeta} - Presente")
        else:
            print(f"❌ {carpeta} - FALTANTE")
            # Intentar copiar manualmente
            try:
                if os.path.exists(carpeta):
                    shutil.copytree(carpeta, carpeta_path)
                    print(f"🔧 {carpeta} copiada manualmente")
            except Exception as e:
                print(f"⚠️ No se pudo copiar {carpeta}: {e}")
    
    # Crear archivo de información
    info_file = os.path.join(dist_dir, "VmPOS_Info.txt")
    with open(info_file, 'w', encoding='utf-8') as f:
        f.write(f"""VmPOS - Sistema de Punto de Venta
Compilado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

INSTRUCCIONES DE INSTALACIÓN:
1. Copiar toda la carpeta VmPOS al destino deseado
2. Ejecutar VmPOS.exe
3. Si hay problemas con la voz, instalar Microsoft Speech Platform
4. Para reportes PDF, verificar permisos de escritura en la carpeta

USUARIOS POR DEFECTO:
- admin / admin123 (Administrador)
- eduardo / 2121 (Administrador)
- andres / 2180 (Vendedor)

SOPORTE:
- Teléfono: +573215545788
- Ubicación: Puerto Colombia

¡Gracias por usar VmPOS!
""")
    
    print(f"✅ Archivo de información creado: {info_file}")
    
    # Mostrar tamaño del directorio
    try:
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(dist_dir):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
        
        size_mb = total_size / (1024 * 1024)
        print(f"📊 Tamaño total de la aplicación: {size_mb:.1f} MB")
    except Exception as e:
        print(f"⚠️ No se pudo calcular el tamaño: {e}")
    
    return True

def main():
    """Función principal del script de compilación"""
    print("🌸 VmPOS - Script de Compilación Automática")
    print("=" * 50)
    
    # Paso 1: Verificar dependencias
    print("\n📋 Paso 1: Verificando dependencias...")
    if not verificar_dependencias():
        print("❌ Faltan dependencias. Instálalas antes de continuar.")
        return False
    
    # Paso 2: Limpiar compilaciones anteriores
    print("\n🧹 Paso 2: Limpiando compilaciones anteriores...")
    limpiar_compilaciones_anteriores()
    
    # Paso 3: Ejecutar correcciones
    print("\n🔧 Paso 3: Aplicando correcciones...")
    try:
        subprocess.run([sys.executable, "fix_imports.py"], check=True)
        print("✅ Correcciones aplicadas")
    except Exception as e:
        print(f"⚠️ Error en correcciones: {e}")
    
    # Paso 4: Compilar
    print("\n🚀 Paso 4: Compilando aplicación...")
    if not compilar_aplicacion():
        print("❌ Error durante la compilación")
        return False
    
    # Paso 5: Post-compilación
    print("\n🔧 Paso 5: Tareas post-compilación...")
    if not post_compilacion():
        print("❌ Error en tareas post-compilación")
        return False
    
    print("\n🎉 ¡COMPILACIÓN COMPLETADA EXITOSAMENTE!")
    print("📁 El ejecutable está en: dist/VmPOS/")
    print("🚀 Ejecuta VmPOS.exe para probar la aplicación")
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Compilación cancelada por el usuario")
    except Exception as e:
        print(f"\n💥 Error inesperado: {e}")
        print("🔧 Revisa la configuración e intenta nuevamente")