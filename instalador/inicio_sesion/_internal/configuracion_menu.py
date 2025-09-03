import tkinter as tk
from tkinter import messagebox, filedialog
import os
import shutil
import sqlite3
import sys
from datetime import datetime

# Configuración de rutas para PyInstaller
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Importación opcional de pandas
try:
    import pandas as pd
    PANDAS_DISPONIBLE = True
except ImportError:
    print("Warning: Pandas no disponible, algunas funciones de exportación estarán limitadas")
    PANDAS_DISPONIBLE = False

def abrir_config(tipo):
    """
    Handles the opening of different configuration functionalities based on 'tipo'.
    """
    if tipo == "restaurar_db":
        restaurar_base_datos()
    elif tipo == "backup_db":
        crear_backup()
    elif tipo == "limpiar_logs":
        limpiar_logs()
    elif tipo == "actualizar_sistema":
        actualizar_sistema()
    elif tipo == "configurar_impresora":
        configurar_impresora()
    elif tipo == "exportar_datos":
        exportar_datos()

def obtener_tablas_db(db_path):
    """
    Obtiene la lista de tablas en la base de datos.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tablas = [tabla[0] for tabla in cursor.fetchall()]
        conn.close()
        return tablas
    except Exception as e:
        print(f"Error al obtener tablas: {e}")
        return []

def verificar_integridad_db(db_path):
    """
    Verifica la integridad de la base de datos antes de realizar operaciones críticas.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar integridad
        cursor.execute("PRAGMA integrity_check;")
        resultado = cursor.fetchone()[0]
        
        conn.close()
        return resultado == "ok"
    except Exception as e:
        print(f"Error verificando integridad: {e}")
        return False

def restaurar_base_datos():
    """
    Elimina todos los datos de todas las tablas en la base de datos ventas.db
    con verificaciones de seguridad mejoradas.
    """
    db_path = "ventas.db"
    
    # Verificar si existe la base de datos
    if not os.path.exists(db_path):
        messagebox.showerror("❌ Error", 
                           f"La base de datos '{db_path}' no existe.\n"
                           f"Ubicación buscada: {os.path.abspath(db_path)}\n"
                           "Verifica la ubicación del archivo.")
        return
    
    # Verificar integridad antes de continuar
    if not verificar_integridad_db(db_path):
        messagebox.showerror("❌ Error de Integridad", 
                           "La base de datos parece estar corrupta.\n"
                           "Por seguridad, no se realizará la restauración.\n"
                           "Intenta reparar la base de datos primero.")
        return
    
    # Obtener información de las tablas
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Obtener tablas de usuario
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tablas_disponibles = [tabla[0] for tabla in cursor.fetchall()]
        
        # Contar registros totales
        total_registros = 0
        info_tablas = []
        
        for tabla in tablas_disponibles:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM [{tabla}]")
                count = cursor.fetchone()[0]
                total_registros += count
                info_tablas.append(f"• {tabla}: {count} registros")
            except Exception as e:
                info_tablas.append(f"• {tabla}: Error al contar")
        
        conn.close()
        
        if not tablas_disponibles:
            messagebox.showwarning("⚠️ Advertencia", 
                                 f"No se encontraron tablas en la base de datos.\n"
                                 f"La base de datos podría estar vacía.\n\n"
                                 f"Usa el 🔧 Diagnóstico para más información.")
            return
            
    except Exception as e:
        messagebox.showerror("❌ Error", 
                           f"No se puede leer la base de datos:\n{str(e)}")
        return
    
    # Mostrar diálogo de confirmación detallado
    info_texto = "\n".join(info_tablas)
    respuesta = messagebox.askyesno(
        "💖 Restaurar Base de Datos",
        f"¿ESTÁS SEGURA de que deseas ELIMINAR todos los datos?\n\n"
        f"📊 RESUMEN DE DATOS A ELIMINAR:\n"
        f"📋 Tablas encontradas: {len(tablas_disponibles)}\n"
        f"📈 Total de registros: {total_registros}\n\n"
        f"DETALLES:\n{info_texto}\n\n"
        f"⚠️ ESTA ACCIÓN NO SE PUEDE DESHACER\n"
        f"✅ Se creará un backup automático antes de continuar\n\n"
        f"¿Continuar con la restauración?"
    )
    
    if not respuesta:
        return
    
    # Segunda confirmación para operaciones críticas
    if total_registros > 100:  # Si hay muchos registros, pedir confirmación adicional
        confirmacion_final = messagebox.askyesno(
            "🚨 CONFIRMACIÓN FINAL",
            f"⚠️ ÚLTIMA ADVERTENCIA ⚠️\n\n"
            f"Vas a eliminar {total_registros} registros permanentemente.\n\n"
            f"¿Estás COMPLETAMENTE SEGURA?\n"
            f"Escribe 'SI' mentalmente y confirma.",
            icon="warning"
        )
        
        if not confirmacion_final:
            messagebox.showinfo("✅ Operación Cancelada", 
                              "La restauración ha sido cancelada.\n"
                              "Tus datos están seguros.")
            return
    
    conn = None
    try:
        # Crear backup automático antes de restaurar
        fecha_backup = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_antes_restaurar_{fecha_backup}.db"
        backup_dir = "./backups"
        os.makedirs(backup_dir, exist_ok=True)
        backup_path = os.path.join(backup_dir, backup_name)
        
        # Crear backup
        shutil.copy2(db_path, backup_path)
        
        # Verificar que el backup se creó correctamente
        if not os.path.exists(backup_path):
            raise Exception("No se pudo crear el backup de seguridad")
        
        # Conectar a la base de datos
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = OFF")  # Deshabilitar foreign keys temporalmente
        cursor = conn.cursor()
        
        # Comenzar transacción
        cursor.execute("BEGIN TRANSACTION;")
        
        # Obtener todas las tablas nuevamente
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tablas = [tabla[0] for tabla in cursor.fetchall()]
        
        tablas_resultado = []
        total_eliminados = 0
        errores = []
        
        # Eliminar datos de cada tabla
        for tabla in tablas:
            try:
                # Contar registros antes de eliminar
                cursor.execute(f"SELECT COUNT(*) FROM [{tabla}]")
                registros_antes = cursor.fetchone()[0]
                
                # Eliminar todos los datos de la tabla
                cursor.execute(f"DELETE FROM [{tabla}]")
                
                # Verificar eliminación
                cursor.execute(f"SELECT COUNT(*) FROM [{tabla}]")
                registros_despues = cursor.fetchone()[0]
                
                eliminados = registros_antes - registros_despues
                total_eliminados += eliminados
                
                if registros_despues == 0:
                    tablas_resultado.append(f"✅ {tabla}: {registros_antes} registros eliminados")
                else:
                    tablas_resultado.append(f"⚠️ {tabla}: {eliminados} eliminados, {registros_despues} restantes")
                        
            except Exception as e:
                error_msg = f"❌ {tabla}: Error - {str(e)}"
                tablas_resultado.append(error_msg)
                errores.append(error_msg)
        
        # Resetear secuencias de autoincrement
        try:
            cursor.execute("DELETE FROM sqlite_sequence")
            cursor.execute("UPDATE sqlite_sequence SET seq = 0")
        except Exception as e:
            print(f"Info: No se pudo resetear sqlite_sequence: {e}")
        
        # Si hay errores críticos, hacer rollback
        if len(errores) > len(tablas) / 2:  # Si más del 50% falló
            conn.rollback()
            raise Exception(f"Demasiados errores durante la eliminación: {len(errores)} de {len(tablas)} tablas fallaron")
        
        # Confirmar cambios
        conn.commit()
        
        # Ejecutar VACUUM para optimizar la base de datos
        try:
            cursor.execute("VACUUM")
        except Exception as e:
            print(f"Info: No se pudo ejecutar VACUUM: {e}")
        
        conn.close()
        conn = None
        
        # Verificar el resultado final
        conn_verify = sqlite3.connect(db_path)
        cursor_verify = conn_verify.cursor()
        
        registros_finales = 0
        for tabla in tablas:
            try:
                cursor_verify.execute(f"SELECT COUNT(*) FROM [{tabla}]")
                count = cursor_verify.fetchone()[0]
                registros_finales += count
            except:
                pass
        
        conn_verify.close()
        
        # Mostrar resultados detallados
        mostrar_resultado_restauracion(tablas_resultado, total_eliminados, registros_finales, backup_name, errores)
        
    except Exception as e:
        if conn:
            try:
                conn.rollback()
                conn.close()
            except:
                pass
        
        messagebox.showerror("❌ Error Crítico", 
                            f"No se pudo completar la restauración:\n\n"
                            f"Error: {str(e)}\n"
                            f"Tipo: {type(e).__name__}\n\n"
                            f"La base de datos no ha sido modificada.\n"
                            f"Tus datos están seguros.")
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass

def mostrar_resultado_restauracion(tablas_resultado, total_eliminados, registros_finales, backup_name, errores):
    """
    Muestra una ventana detallada con los resultados de la restauración.
    """
    resultado_window = tk.Toplevel()
    resultado_window.title("✅ Resultado de la Restauración")
    resultado_window.geometry("700x500")
    resultado_window.configure(bg="#FFE4F1")
    resultado_window.resizable(True, True)
    resultado_window.grab_set()  # Modal
    
    main_frame = tk.Frame(resultado_window, bg="#FFE4F1")
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Título con estado
    if registros_finales == 0 and not errores:
        titulo = "✅ RESTAURACIÓN COMPLETADA EXITOSAMENTE"
        color_titulo = "#32CD32"
    elif registros_finales == 0 and errores:
        titulo = "⚠️ RESTAURACIÓN COMPLETADA CON ADVERTENCIAS"
        color_titulo = "#FF8C00"
    else:
        titulo = "❌ RESTAURACIÓN INCOMPLETA"
        color_titulo = "#FF6347"
    
    title_label = tk.Label(main_frame, text=titulo, 
                          font=("Segoe UI", 16, "bold"), 
                          bg="#FFE4F1", fg=color_titulo)
    title_label.pack(pady=(0, 15))
    
    # Información resumida
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    resumen_text = (f"🕐 Fecha: {fecha_actual}\n"
                   f"📊 Registros eliminados: {total_eliminados}\n"
                   f"📊 Registros restantes: {registros_finales}\n"
                   f"💾 Backup creado: {backup_name}\n"
                   f"⚠️ Errores: {len(errores)}")
    
    resumen_label = tk.Label(main_frame, text=resumen_text, 
                           font=("Segoe UI", 11), 
                           bg="#FFE4F1", fg="#333333", justify="left")
    resumen_label.pack(pady=(0, 15))
    
    # Detalles por tabla en texto scrollable
    details_label = tk.Label(main_frame, text="📋 DETALLES POR TABLA:", 
                           font=("Segoe UI", 12, "bold"), 
                           bg="#FFE4F1", fg="#FF1493")
    details_label.pack(anchor="w", pady=(0, 5))
    
    text_frame = tk.Frame(main_frame, bg="#FFE4F1")
    text_frame.pack(fill="both", expand=True)
    
    scrollbar = tk.Scrollbar(text_frame)
    scrollbar.pack(side="right", fill="y")
    
    text_widget = tk.Text(text_frame, wrap="word", yscrollcommand=scrollbar.set,
                         font=("Consolas", 10), bg="white", fg="#333333",
                         relief="solid", bd=1)
    text_widget.pack(fill="both", expand=True)
    scrollbar.config(command=text_widget.yview)
    
    detalles_texto = "\n".join(tablas_resultado)
    if errores:
        detalles_texto += "\n\n❌ ERRORES ENCONTRADOS:\n" + "\n".join(errores)
    
    text_widget.insert("1.0", detalles_texto)
    text_widget.config(state="disabled")
    
    # Botones
    buttons_frame = tk.Frame(main_frame, bg="#FFE4F1")
    buttons_frame.pack(pady=(15, 0))
    
    # Botón cerrar
    close_btn = tk.Button(buttons_frame, text="✅ Aceptar", command=resultado_window.destroy,
                         bg="#32CD32", fg="white", font=("Segoe UI", 12, "bold"),
                         padx=20, pady=10)
    close_btn.pack(side="left", padx=(0, 10))
    
    # Botón para abrir carpeta de backups
    def abrir_carpeta_backup():
        try:
            backup_dir = os.path.abspath("./backups")
            if os.path.exists(backup_dir):
                os.startfile(backup_dir)  # Windows
            else:
                messagebox.showinfo("📁", f"Carpeta de backups:\n{backup_dir}")
        except:
            messagebox.showinfo("📁", f"Carpeta de backups:\n{os.path.abspath('./backups')}")
    
    backup_btn = tk.Button(buttons_frame, text="📁 Ver Backups", command=abrir_carpeta_backup,
                          bg="#4169E1", fg="white", font=("Segoe UI", 12, "bold"),
                          padx=20, pady=10)
    backup_btn.pack(side="left")

def crear_backup():
    """
    Crea una copia de seguridad completa de la base de datos ventas.db
    con verificaciones mejoradas y opciones avanzadas.
    """
    db_path = "ventas.db"
    
    # Verificar si existe la base de datos
    if not os.path.exists(db_path):
        messagebox.showerror("❌ Error", 
                           f"La base de datos '{db_path}' no existe.\n"
                           f"Ubicación buscada: {os.path.abspath(db_path)}\n"
                           "No se puede crear el backup.")
        return
    
    # Verificar integridad de la base de datos
    if not verificar_integridad_db(db_path):
        respuesta = messagebox.askyesno("⚠️ Advertencia de Integridad",
                                       "La base de datos podría tener problemas de integridad.\n"
                                       "El backup se puede crear, pero podría no ser confiable.\n\n"
                                       "¿Deseas continuar con el backup?")
        if not respuesta:
            return
    
    try:
        # Obtener información de la base de datos antes del backup
        file_size = os.path.getsize(db_path)
        size_mb = round(file_size / 1024 / 1024, 2)
        
        tablas = obtener_tablas_db(db_path)
        num_tablas = len([t for t in tablas if t != 'sqlite_sequence'])
        
        # Contar registros totales
        total_registros = 0
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            for tabla in tablas:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM [{tabla}]")
                    count = cursor.fetchone()[0]
                    total_registros += count
                except:
                    pass
            
            conn.close()
        except:
            total_registros = "Desconocido"
        
        # Crear directorio de backups si no existe
        backup_dir = "./backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generar nombre del backup con fecha y hora
        fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_backup = f"backup_vmpos_{fecha}.db"
        backup_path = os.path.join(backup_dir, nombre_backup)
        
        # Mostrar progreso (simulado)
        progress_window = tk.Toplevel()
        progress_window.title("💾 Creando Backup...")
        progress_window.geometry("400x200")
        progress_window.configure(bg="#FFE4F1")
        progress_window.resizable(False, False)
        progress_window.grab_set()
        
        # Centrar ventana de progreso
        progress_window.update_idletasks()
        x = (progress_window.winfo_screenwidth() // 2) - 200
        y = (progress_window.winfo_screenheight() // 2) - 100
        progress_window.geometry(f"400x200+{x}+{y}")
        
        progress_frame = tk.Frame(progress_window, bg="#FFE4F1")
        progress_frame.pack(expand=True, fill="both", padx=30, pady=30)
        
        tk.Label(progress_frame, text="💾 Creando Backup...", 
                font=("Segoe UI", 14, "bold"), bg="#FFE4F1", fg="#FF1493").pack(pady=20)
        
        progress_label = tk.Label(progress_frame, text="Iniciando...", 
                                font=("Segoe UI", 10), bg="#FFE4F1", fg="#666666")
        progress_label.pack(pady=10)
        
        # Actualizar interfaz
        progress_window.update()
        
        # Paso 1: Verificar espacio disponible
        progress_label.config(text="Verificando espacio disponible...")
        progress_window.update()
        
        # Obtener espacio libre en disco
        try:
            stat = shutil.disk_usage(backup_dir)
            espacio_libre = stat.free / 1024 / 1024  # MB
            
            if espacio_libre < size_mb * 2:  # Necesitamos al menos el doble del tamaño
                progress_window.destroy()
                messagebox.showerror("❌ Espacio Insuficiente",
                                   f"No hay suficiente espacio en disco.\n"
                                   f"Espacio necesario: ~{size_mb * 2:.1f} MB\n"
                                   f"Espacio disponible: {espacio_libre:.1f} MB")
                return
        except:
            pass  # Si no se puede verificar, continuar
        
        # Paso 2: Crear el backup
        progress_label.config(text="Copiando base de datos...")
        progress_window.update()
        
        # Crear el backup usando copy2 para preservar metadatos
        shutil.copy2(db_path, backup_path)
        
        # Paso 3: Verificar integridad del backup
        progress_label.config(text="Verificando backup...")
        progress_window.update()
        
        backup_valido = verificar_integridad_db(backup_path)
        
        # Obtener información del backup creado
        backup_size = os.path.getsize(backup_path)
        backup_size_mb = round(backup_size / 1024 / 1024, 2)
        
        progress_window.destroy()
        
        # Mostrar resultado detallado
        if backup_valido:
            icono_estado = "✅"
            estado = "EXITOSO"
            color_estado = "#32CD32"
            mensaje_extra = "El backup se creó correctamente y pasó la verificación de integridad."
        else:
            icono_estado = "⚠️"
            estado = "CON ADVERTENCIAS"
            color_estado = "#FF8C00"
            mensaje_extra = "El backup se creó pero hay advertencias de integridad."
        
        # Ventana de resultado personalizada
        resultado_window = tk.Toplevel()
        resultado_window.title(f"{icono_estado} Backup {estado}")
        resultado_window.geometry("500x400")
        resultado_window.configure(bg="#FFE4F1")
        resultado_window.resizable(False, False)
        resultado_window.grab_set()
        
        # Centrar ventana
        resultado_window.update_idletasks()
        x = (resultado_window.winfo_screenwidth() // 2) - 250
        y = (resultado_window.winfo_screenheight() // 2) - 200
        resultado_window.geometry(f"500x400+{x}+{y}")
        
        main_frame = tk.Frame(resultado_window, bg="#FFE4F1")
        main_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Título
        title_label = tk.Label(main_frame, text=f"{icono_estado} BACKUP {estado}", 
                              font=("Segoe UI", 16, "bold"), 
                              bg="#FFE4F1", fg=color_estado)
        title_label.pack(pady=(0, 20))
        
        # Información del backup
        info_frame = tk.Frame(main_frame, bg="white", relief="solid", bd=1)
        info_frame.pack(fill="x", pady=(0, 20))
        
        info_content = tk.Frame(info_frame, bg="white")
        info_content.pack(fill="both", expand=True, padx=20, pady=15)
        
        # Detalles del backup
        detalles = [
            ("📁 Archivo:", nombre_backup),
            ("📅 Fecha:", datetime.now().strftime('%d/%m/%Y %H:%M:%S')),
            ("💾 Tamaño:", f"{backup_size_mb} MB"),
            ("📋 Tablas:", str(num_tablas)),
            ("📊 Registros:", str(total_registros)),
            ("✅ Estado:", "Verificado" if backup_valido else "Con advertencias"),
            ("📂 Ubicación:", os.path.dirname(backup_path))
        ]
        
        for i, (etiqueta, valor) in enumerate(detalles):
            detail_frame = tk.Frame(info_content, bg="white")
            detail_frame.pack(fill="x", pady=2)
            
            tk.Label(detail_frame, text=etiqueta, font=("Segoe UI", 10, "bold"),
                    bg="white", fg="#666666").pack(side="left")
            tk.Label(detail_frame, text=valor, font=("Segoe UI", 10),
                    bg="white", fg="#333333").pack(side="left", padx=(10, 0))
        
        # Mensaje adicional
        tk.Label(main_frame, text=mensaje_extra, font=("Segoe UI", 10),
                bg="#FFE4F1", fg="#666666", wraplength=440, justify="center").pack(pady=(0, 20))
        
        # Botones
        buttons_frame = tk.Frame(main_frame, bg="#FFE4F1")
        buttons_frame.pack(fill="x")
        
        # Botón aceptar
        accept_btn = tk.Button(buttons_frame, text="✅ Aceptar", 
                              command=resultado_window.destroy,
                              bg=color_estado, fg="white", 
                              font=("Segoe UI", 12, "bold"),
                              padx=20, pady=10)
        accept_btn.pack(side="right")
        
        # Botón abrir carpeta
        def abrir_carpeta():
            try:
                backup_dir_abs = os.path.abspath(backup_dir)
                os.startfile(backup_dir_abs)
            except:
                messagebox.showinfo("📁 Ubicación", f"Carpeta de backups:\n{os.path.abspath(backup_dir)}")
        
        folder_btn = tk.Button(buttons_frame, text="📁 Abrir Carpeta", 
                              command=abrir_carpeta,
                              bg="#4169E1", fg="white", 
                              font=("Segoe UI", 12, "bold"),
                              padx=20, pady=10)
        folder_btn.pack(side="right", padx=(0, 10))
    
    except Exception as e:
        messagebox.showerror("❌ Error", 
                           f"No se pudo crear el backup:\n\n{str(e)}\n\n"
                           f"Tipo de error: {type(e).__name__}")

def diagnosticar_base_datos():
    """
    Muestra información detallada sobre la base de datos y sus tablas
    """
    db_path = "ventas.db"
    
    if not os.path.exists(db_path):
        messagebox.showerror("❌ Error", f"La base de datos '{db_path}' no existe en el directorio actual.")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Obtener TODAS las entradas de sqlite_master
        cursor.execute("SELECT type, name, sql FROM sqlite_master")
        todas_entradas = cursor.fetchall()
        
        # Obtener información de todas las tablas (incluyendo sqlite_%)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        todas_las_tablas = [tabla[0] for tabla in cursor.fetchall()]
        
        # Obtener solo tablas de usuario
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tablas_usuario = [tabla[0] for tabla in cursor.fetchall()]
        
        info_completa = []
        info_completa.append(f"📁 Archivo: {os.path.abspath(db_path)}")
        info_completa.append(f"📊 Tamaño: {os.path.getsize(db_path)} bytes")
        info_completa.append(f"📋 Total entradas sqlite_master: {len(todas_entradas)}")
        info_completa.append(f"📋 Tablas del sistema: {len(todas_las_tablas) - len(tablas_usuario)}")
        info_completa.append(f"📋 Tablas de usuario: {len(tablas_usuario)}")
        info_completa.append("")
        
        if todas_entradas:
            info_completa.append("🔍 TODAS LAS ENTRADAS EN sqlite_master:")
            for tipo, nombre, sql in todas_entradas:
                info_completa.append(f"  {tipo}: {nombre}")
        else:
            info_completa.append("⚠️ No hay entradas en sqlite_master")
        
        info_completa.append("")
        
        if tablas_usuario:
            info_completa.append("📊 DETALLES DE TABLAS DE USUARIO:")
            total_registros = 0
            
            for tabla in tablas_usuario:
                try:
                    # Contar registros
                    cursor.execute(f"SELECT COUNT(*) FROM [{tabla}]")
                    count = cursor.fetchone()[0]
                    total_registros += count
                    
                    # Obtener información de columnas
                    cursor.execute(f"PRAGMA table_info([{tabla}])")
                    columnas = cursor.fetchall()
                    num_columnas = len(columnas)
                    
                    # Obtener algunos nombres de columnas
                    nombres_columnas = [col[1] for col in columnas[:5]]  # Primeras 5 columnas
                    columnas_texto = ", ".join(nombres_columnas)
                    if len(columnas) > 5:
                        columnas_texto += "..."
                    
                    info_completa.append(f"  📋 {tabla}:")
                    info_completa.append(f"    • Registros: {count}")
                    info_completa.append(f"    • Columnas: {num_columnas}")
                    info_completa.append(f"    • Campos: {columnas_texto}")
                    
                except Exception as e:
                    info_completa.append(f"  ❌ {tabla}: Error - {str(e)}")
            
            info_completa.append(f"\n📊 TOTAL REGISTROS: {total_registros}")
        else:
            info_completa.append("⚠️ NO SE ENCONTRARON TABLAS DE USUARIO")
        
        conn.close()
        
        # Mostrar información en una ventana de texto scrollable
        info_window = tk.Toplevel()
        info_window.title("🔍 Diagnóstico Completo - Base de Datos")
        info_window.geometry("700x500")
        info_window.configure(bg="#FFE4F1")
        
        # Frame principal
        main_frame = tk.Frame(info_window, bg="#FFE4F1")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        title_label = tk.Label(main_frame, text="🔍 DIAGNÓSTICO COMPLETO", 
                              font=("Segoe UI", 16, "bold"), 
                              bg="#FFE4F1", fg="#FF1493")
        title_label.pack(pady=(0, 15))
        
        # Text widget con scrollbar
        text_frame = tk.Frame(main_frame, bg="#FFE4F1")
        text_frame.pack(fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")
        
        text_widget = tk.Text(text_frame, wrap="word", yscrollcommand=scrollbar.set,
                             font=("Consolas", 10), bg="white", fg="#333333")
        text_widget.pack(fill="both", expand=True)
        scrollbar.config(command=text_widget.yview)
        
        # Insertar el texto
        info_texto = "\n".join(info_completa)
        text_widget.insert("1.0", info_texto)
        text_widget.config(state="disabled")
        
        # Botón cerrar
        close_btn = tk.Button(main_frame, text="❌ Cerrar", command=info_window.destroy,
                             bg="#FF1493", fg="white", font=("Segoe UI", 12, "bold"),
                             padx=20, pady=10)
        close_btn.pack(pady=(15, 0))
        
    except Exception as e:
        messagebox.showerror("❌ Error", f"Error al diagnosticar la base de datos:\n{str(e)}\n\nTipo: {type(e).__name__}")

def exportar_datos():
    """
    Exporta las tablas de productos, ventas y clientes a un archivo Excel estructurado
    """
    db_path = "ventas.db"
    
    # Verificar si existe la base de datos
    if not os.path.exists(db_path):
        messagebox.showerror("❌ Error", 
                           f"La base de datos '{db_path}' no existe.\n"
                           "No se pueden exportar los datos.")
        return
    
    # Seleccionar ubicación para guardar el archivo
    fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"exportacion_vmpos_{fecha}.xlsx"
    
    archivo_destino = filedialog.asksaveasfilename(
        title="💾 Guardar Exportación",
        defaultextension=".xlsx",
        initialfilename=nombre_archivo,
        filetypes=[
            ("Excel files", "*.xlsx"),
            ("All files", "*.*")
        ]
    )
    
    if not archivo_destino:
        return  # Usuario canceló
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Obtener todas las tablas disponibles
        tablas_disponibles = obtener_tablas_db(db_path)
        tablas_objetivo = ['productos', 'ventas', 'clientes']
        
        # Crear el archivo Excel con múltiples hojas
        with pd.ExcelWriter(archivo_destino, engine='openpyxl') as writer:
            tablas_exportadas = []
            datos_resumen = []
            
            # Exportar cada tabla objetivo si existe
            for tabla in tablas_objetivo:
                # Buscar tabla con nombres similares (case insensitive)
                tabla_encontrada = None
                for t in tablas_disponibles:
                    if t.lower() == tabla.lower() or tabla.lower() in t.lower():
                        tabla_encontrada = t
                        break
                
                if tabla_encontrada:
                    try:
                        # Leer datos de la tabla
                        df = pd.read_sql_query(f"SELECT * FROM {tabla_encontrada}", conn)
                        
                        if not df.empty:
                            # Escribir a Excel con formato
                            sheet_name = tabla.capitalize()
                            df.to_excel(writer, sheet_name=sheet_name, index=False)
                            
                            # Formatear la hoja
                            worksheet = writer.sheets[sheet_name]
                            
                            # Ajustar ancho de columnas
                            for column in worksheet.columns:
                                max_length = 0
                                column_letter = column[0].column_letter
                                for cell in column:
                                    try:
                                        if len(str(cell.value)) > max_length:
                                            max_length = len(str(cell.value))
                                    except:
                                        pass
                                adjusted_width = min(max_length + 2, 50)
                                worksheet.column_dimensions[column_letter].width = adjusted_width
                            
                            tablas_exportadas.append(tabla_encontrada)
                            datos_resumen.append({
                                'Tabla': tabla_encontrada,
                                'Registros': len(df),
                                'Columnas': len(df.columns)
                            })
                    
                    except Exception as e:
                        print(f"Error exportando tabla {tabla_encontrada}: {e}")
                        datos_resumen.append({
                            'Tabla': tabla_encontrada,
                            'Registros': 'Error',
                            'Columnas': 'Error'
                        })
            
            # Crear hoja de resumen
            if datos_resumen:
                df_resumen = pd.DataFrame(datos_resumen)
                df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
                
                # Formatear hoja de resumen
                worksheet_resumen = writer.sheets['Resumen']
                for column in worksheet_resumen.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = max_length + 2
                    worksheet_resumen.column_dimensions[column_letter].width = adjusted_width
        
        conn.close()
        
        # Mostrar resultado
        if tablas_exportadas:
            total_registros = sum([r['Registros'] for r in datos_resumen if isinstance(r['Registros'], int)])
            messagebox.showinfo("✅ Exportación Completa", 
                              f"📊 ¡Datos exportados exitosamente!\n\n"
                              f"📁 Archivo: {os.path.basename(archivo_destino)}\n"
                              f"📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
                              f"📋 Tablas exportadas: {len(tablas_exportadas)}\n"
                              f"📈 Total registros: {total_registros}\n"
                              f"💾 Ubicación: {archivo_destino}")
        else:
            messagebox.showwarning("⚠️ Sin Datos", 
                                 "No se encontraron las tablas 'productos', 'ventas' o 'clientes'\n"
                                 f"en la base de datos.\n\n"
                                 f"Tablas disponibles: {', '.join(tablas_disponibles)}")
    
    except Exception as e:
        messagebox.showerror("❌ Error", 
                           f"No se pudieron exportar los datos:\n{str(e)}")

def limpiar_logs():
    """
    Limpia los archivos de log del sistema
    """
    respuesta = messagebox.askyesno(
        "🧹 Limpiar Logs",
        "¿Deseas limpiar todos los archivos de log?\n\n"
        "💡 Esto ayudará a liberar espacio en disco.\n"
        "📋 Se buscarán archivos .log y .txt en la carpeta 'logs'"
    )
    
    if respuesta:
        try:
            logs_dir = "./logs"
            archivos_eliminados = 0
            espacio_liberado = 0
            
            if os.path.exists(logs_dir):
                for filename in os.listdir(logs_dir):
                    if filename.endswith(('.log', '.txt')):
                        file_path = os.path.join(logs_dir, filename)
                        try:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            archivos_eliminados += 1
                            espacio_liberado += file_size
                        except Exception as e:
                            print(f"Error eliminando {filename}: {e}")
            
            espacio_mb = round(espacio_liberado / 1024 / 1024, 2)
            
            messagebox.showinfo("✅ Limpieza Completa", 
                              f"¡Logs eliminados exitosamente! ✨\n\n"
                              f"📁 Archivos eliminados: {archivos_eliminados}\n"
                              f"💾 Espacio liberado: {espacio_mb} MB")
        
        except Exception as e:
            messagebox.showerror("❌ Error", 
                               f"Error durante la limpieza de logs:\n{str(e)}")

def actualizar_sistema():
    """
    Simula la verificación de actualizaciones del sistema
    """
    messagebox.showinfo("🚀 Actualizar Sistema", 
                        "🌟 Verificando actualizaciones...\n\n"
                        "✅ Tu sistema está actualizado\n"
                        "📅 Versión actual: VmPOS v3.1.0\n"
                        "💖 ¡Todo funciona perfectamente!")

def configurar_impresora():
    """
    Simula la configuración de la impresora
    """
    messagebox.showinfo("🖨️ Configurar Impresora", 
                        "⚙️ Abriendo configuración de impresora...\n\n"
                        "💡 Asegúrate de que la impresora esté conectada\n"
                        "🔌 Puerto USB recomendado\n"
                        "📄 Papel térmico 58mm o 80mm")

def crear_cuadro(padre, texto, icono, color, tipo):
    """
    Creates a styled interactive square button for configuration options.
    """
    frame = tk.Frame(padre, width=320, height=160, bg=color, relief="raised", bd=3, cursor="hand2")
    frame.pack_propagate(False)

    # Internal container to center content
    content_frame = tk.Frame(frame, bg=color)
    content_frame.pack(expand=True, fill="both")

    # Large icon
    icon_label = tk.Label(content_frame, text=icono, font=("Segoe UI Emoji", 36), 
                          bg=color, fg="white")
    icon_label.pack(pady=(20, 10))

    # Main text
    text_label = tk.Label(content_frame, text=texto, font=("Segoe UI", 12, "bold"), 
                          bg=color, fg="white", wraplength=280, justify="center")
    text_label.pack(pady=(0, 20))

    # Hover effects
    def on_enter(e):
        frame.config(bg="#FF1493", relief="raised", bd=4)
        content_frame.config(bg="#FF1493")
        icon_label.config(bg="#FF1493")
        text_label.config(bg="#FF1493")

    def on_leave(e):
        frame.config(bg=color, relief="raised", bd=3)
        content_frame.config(bg=color)
        icon_label.config(bg=color)
        text_label.config(bg=color)

    def on_click(e):
        # Click effect
        frame.config(relief="sunken", bd=2)
        frame.after(100, lambda: frame.config(relief="raised", bd=3))
        abrir_config(tipo)

    # Bind events to all elements within the square
    for widget in [frame, content_frame, icon_label, text_label]:
        widget.bind("<Button-1>", on_click)
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    return frame

def iniciar_configuracion():
    """
    Initializes and displays the main configuration window.
    """
    ventana = tk.Tk()
    ventana.title("⚙️ Configuración - VmPOS")
    ventana.geometry("1100x700")
    ventana.configure(bg="#FFE4F1")
    ventana.resizable(False, False)
    
    # Center window
    ventana.update_idletasks()
    x = (ventana.winfo_screenwidth() // 2) - (550)
    y = (ventana.winfo_screenheight() // 2) - (350)
    ventana.geometry(f"1100x700+{x}+{y}")

    # 🌸 Header principal con gradiente
    header_frame = tk.Frame(ventana, bg="#FF1493", height=100)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)

    # Header content
    header_content = tk.Frame(header_frame, bg="#FF1493")
    header_content.pack(expand=True, fill="both")

    title_container = tk.Frame(header_content, bg="#FF1493")
    title_container.pack(expand=True)

    tk.Label(title_container, text="⚙️", font=("Segoe UI Emoji", 40), 
             bg="#FF1493", fg="white").pack(side="left", pady=25, padx=(50, 15))
    tk.Label(title_container, text="CONFIGURACIÓN DEL SISTEMA", font=("Segoe UI", 22, "bold"), 
             bg="#FF1493", fg="white").pack(side="left", pady=30)
    tk.Label(title_container, text="✨", font=("Segoe UI Emoji", 40), 
             bg="#FF1493", fg="white").pack(side="left", pady=25, padx=(15, 50))

    # 💖 Subtitle
    subtitle_frame = tk.Frame(ventana, bg="#FFDDEE", height=60)
    subtitle_frame.pack(fill="x")
    subtitle_frame.pack_propagate(False)

    tk.Label(subtitle_frame, text="🌸 Personaliza y mantén tu sistema siempre actualizado 🌸", 
             font=("Segoe UI", 14), bg="#FFDDEE", fg="#C71585").pack(expand=True)

    # 🎀 Main configuration panel
    main_panel = tk.Frame(ventana, bg="#FFE4F1")
    main_panel.pack(fill="both", expand=True, pady=30, padx=40)

    # 📊 System information panel
    info_frame = tk.Frame(main_panel, bg="#FFC0CB", relief="raised", bd=2, height=100)
    info_frame.pack(fill="x", pady=(0, 30))
    info_frame.pack_propagate(False)

    info_content = tk.Frame(info_frame, bg="#FFC0CB")
    info_content.pack(expand=True, fill="both", padx=30, pady=20)

    # System information in columns
    col1 = tk.Frame(info_content, bg="#FFC0CB")
    col1.pack(side="left", fill="both", expand=True)

    col2 = tk.Frame(info_content, bg="#FFC0CB")
    col2.pack(side="left", fill="both", expand=True)

    col3 = tk.Frame(info_content, bg="#FFC0CB")
    col3.pack(side="left", fill="both", expand=True)

    # System information labels
    tk.Label(col1, text="💻 Sistema", font=("Segoe UI", 10, "bold"), 
             bg="#FFC0CB", fg="#8B0054").pack()
    tk.Label(col1, text="VmPOS v3.1.0", font=("Segoe UI", 12), 
             bg="#FFC0CB", fg="#FF1493").pack()

    tk.Label(col2, text="📅 Última Actualización", font=("Segoe UI", 10, "bold"), 
             bg="#FFC0CB", fg="#8B0054").pack()
    tk.Label(col2, text="01/08/2025", font=("Segoe UI", 12), 
             bg="#FFC0CB", fg="#FF1493").pack()

    tk.Label(col3, text="💾 Base de Datos", font=("Segoe UI", 10, "bold"), 
             bg="#FFC0CB", fg="#8B0054").pack()
    tk.Label(col3, text="Conectada ✅", font=("Segoe UI", 12), 
             bg="#FFC0CB", fg="#32CD32").pack()

    # 🎨 Configuration options panel in a grid-like fashion
    options_container = tk.Frame(main_panel, bg="#FFE4F1")
    options_container.pack(fill="both", expand=True)

    # Options organized in rows
    opciones = [
        # First row
        [
            ("🔄 Restaurar\nBase de Datos", "🔄", "#FF6B6B", "restaurar_db"),
            ("💾 Crear Copia\nde Seguridad", "💾", "#4ECDC4", "backup_db"),
            ("🧹 Limpiar\nArchivos Log", "🧹", "#45B7D1", "limpiar_logs")
        ],
        # Second row
        [
            ("🚀 Actualizar\nSistema", "🚀", "#96CEB4", "actualizar_sistema"),
            ("🖨️ Configurar\nImpresora", "🖨️", "#FECA57", "configurar_impresora"),
            ("📊 Exportar\nDatos", "📊", "#FF9FF3", "exportar_datos")
        ]
    ]

    for fila_opciones in opciones:
        fila_frame = tk.Frame(options_container, bg="#FFE4F1")
        fila_frame.pack(pady=20)
        
        for texto, icono, color, tipo in fila_opciones:
            cuadro = crear_cuadro(fila_frame, texto, icono, color, tipo)
            cuadro.pack(side="left", padx=25)

    # 🌟 Quick actions panel
    quick_actions_frame = tk.Frame(ventana, bg="#FF1493", height=80)
    quick_actions_frame.pack(fill="x")
    quick_actions_frame.pack_propagate(False)

    quick_content = tk.Frame(quick_actions_frame, bg="#FF1493")
    quick_content.pack(expand=True, fill="both")

    tk.Label(quick_content, text="⚡ ACCIONES RÁPIDAS", font=("Segoe UI", 12, "bold"), 
             bg="#FF1493", fg="white").pack(side="left", padx=30, pady=25)

    # Quick access buttons
    quick_buttons = [
        ("🔧 Diagnóstico", diagnosticar_base_datos),
        ("📋 Logs del Sistema", lambda: messagebox.showinfo("📋", "Mostrando logs recientes...")),
        ("🌐 Verificar Conexión", lambda: messagebox.showinfo("🌐", "Conexión a internet: OK ✅")),
        ("🎨 Cambiar Tema", lambda: messagebox.showinfo("🎨", "Tema femenino activo 💖"))
    ]

    quick_buttons_frame = tk.Frame(quick_content, bg="#FF1493")
    quick_buttons_frame.pack(side="right", padx=30, pady=15)

    for texto, comando in quick_buttons:
        btn = tk.Button(quick_buttons_frame, text=texto, command=comando,
                        bg="#FFDDEE", fg="#C71585", font=("Segoe UI", 9, "bold"),
                        relief="flat", padx=12, pady=8, cursor="hand2")
        btn.pack(side="left", padx=5)

        # Hover effects for quick buttons
        def make_quick_hover(button):
            def on_enter(e):
                button.config(bg="#FF69B4", fg="white")
            def on_leave(e):
                button.config(bg="#FFDDEE", fg="#C71585")
            return on_enter, on_leave

        enter_fx, leave_fx = make_quick_hover(btn)
        btn.bind("<Enter>", enter_fx)
        btn.bind("<Leave>", leave_fx)

    # 🎯 Keyboard events
    def keyboard_shortcuts(event):
        if event.state & 4:   # Ctrl pressed
            key = event.keysym.lower()
            if key == 'b':    # Ctrl+B for backup
                crear_backup()
            elif key == 'r':  # Ctrl+R for restore
                restaurar_base_datos()

    ventana.bind("<Key>", keyboard_shortcuts)

    ventana.mainloop()

if __name__ == "__main__":
    iniciar_configuracion()