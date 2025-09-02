# 🚀 Instrucciones para compilar VmPOS con Auto-Py-to-EXE

## 📋 Pasos previos

### 1. Instalar dependencias
```bash
pip install -r requirements_build.txt
```

### 2. Ejecutar corrección de importaciones
```bash
python fix_imports.py
```

### 3. Generar archivo de configuración
```bash
python build_config.py
```

## 🔧 Configuración en Auto-Py-to-EXE

### Configuración básica:
- **Script Location**: `interface/inicio_sesion.py`
- **Onefile**: ❌ NO (usar Onedir para mejor compatibilidad)
- **Console Window**: ❌ NO (Window Based)
- **Icon**: `assets/Salome.ico`

### 📁 Additional Files (MUY IMPORTANTE):
Agregar estas carpetas/archivos:

```
database -> database
assets -> assets
interface -> interface
modules -> modules
config -> config
backups -> backups
reports_pdf -> reports_pdf
reports_excel -> reports_excel
requirements.txt -> .
```

### 🔍 Hidden Imports (CRÍTICO):
Agregar estos módulos en "Advanced" > "Hidden Imports":

```
pyttsx3
pyttsx3.drivers
pyttsx3.drivers.sapi5
reportlab
reportlab.lib
reportlab.lib.pagesizes
reportlab.platypus
reportlab.lib.styles
reportlab.lib.colors
reportlab.pdfbase
reportlab.pdfgen
matplotlib
matplotlib.pyplot
matplotlib.backends.backend_tkagg
pandas
openpyxl
openpyxl.styles
PIL
PIL.Image
PIL.ImageDraw
sqlite3
tkinter
tkinter.ttk
tkinter.messagebox
escpos
escpos.printer
usb.core
usb.util
win32print
```

### ⚙️ Advanced Options:
- **UPX**: ❌ NO (puede causar problemas)
- **Clean**: ✅ SÍ
- **Strip**: ❌ NO

## 🚨 Problemas comunes y soluciones

### 1. Error "ModuleNotFoundError"
- ✅ Verificar que todos los módulos estén en "Hidden Imports"
- ✅ Usar "Onedir" en lugar de "Onefile"
- ✅ Incluir todas las carpetas en "Additional Files"

### 2. Error con pyttsx3 (voz)
- ✅ Instalar: `pip install pyttsx3`
- ✅ Agregar a Hidden Imports: `pyttsx3`, `pyttsx3.drivers`, `pyttsx3.drivers.sapi5`

### 3. Error con reportes PDF
- ✅ Instalar: `pip install reportlab`
- ✅ Agregar todos los módulos de reportlab a Hidden Imports

### 4. Error con gráficos
- ✅ Instalar: `pip install matplotlib`
- ✅ Agregar: `matplotlib.backends.backend_tkagg`

### 5. Base de datos no encontrada
- ✅ Incluir carpeta `database` en Additional Files
- ✅ Verificar que `ventas.db` y `usuarios.db` estén en la carpeta

## 🎯 Comando PyInstaller directo (alternativo)

Si Auto-Py-to-EXE sigue dando problemas, usa este comando:

```bash
pyinstaller --onedir --windowed --icon=assets/Salome.ico --name=VmPOS --add-data="database;database" --add-data="assets;assets" --add-data="interface;interface" --add-data="modules;modules" --add-data="config;config" --hidden-import=pyttsx3 --hidden-import=reportlab --hidden-import=matplotlib --hidden-import=pandas --hidden-import=openpyxl --hidden-import=PIL --hidden-import=sqlite3 --hidden-import=tkinter --hidden-import=escpos interface/inicio_sesion.py
```

## 📦 Después de compilar

1. **Probar el ejecutable** en una máquina sin Python
2. **Verificar que todas las carpetas** estén en el directorio del ejecutable
3. **Incluir archivos de configuración** si es necesario
4. **Crear un instalador** con herramientas como NSIS o Inno Setup

## 🔧 Solución de problemas post-compilación

### Si la voz no funciona:
- Instalar Microsoft Speech Platform en la máquina destino
- Verificar que Windows tenga voces instaladas

### Si los reportes no funcionan:
- Verificar que las carpetas `reports_pdf` y `reports_excel` existan
- Dar permisos de escritura a la carpeta del programa

### Si la base de datos no funciona:
- Verificar que `database/ventas.db` y `database/usuarios.db` estén presentes
- Dar permisos de escritura a la carpeta `database`

## 📋 Lista de verificación final

- [ ] Todas las dependencias instaladas
- [ ] Importaciones corregidas con `fix_imports.py`
- [ ] Archivo .spec generado con `build_config.py`
- [ ] Todas las carpetas incluidas en Additional Files
- [ ] Todos los módulos en Hidden Imports
- [ ] Modo Onedir seleccionado
- [ ] Console Window deshabilitado
- [ ] Icono configurado
- [ ] Ejecutable probado en máquina limpia