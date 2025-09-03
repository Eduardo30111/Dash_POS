import tkinter as tk
from tkinter import ttk
import subprocess
import datetime
from tkinter import messagebox
import sqlite3
import importlib.util
import os
import sys

# Configuración de rutas para PyInstaller
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

base_dir = BASE_DIR
database_dir = os.path.join(base_dir, 'database')
ruta_db = os.path.join(database_dir, 'ventas.db')

# Intentar importar el generador de códigos de barras
GENERADOR_DISPONIBLE = False
iniciar_generador_barras = None

try:
    from generador_codigo_barras import iniciar_generador_barras
    GENERADOR_DISPONIBLE = True
    print("✅ Generador de códigos de barras disponible")
except ImportError as e:
    print(f"⚠️ Generador de códigos de barras no disponible: {e}")
    GENERADOR_DISPONIBLE = False


# Importaciones con manejo de errores
try:
    from pantalla_carga import mostrar_carga
except ImportError as e:
    print(f"Warning: pantalla_carga module not found: {e}")
    def mostrar_carga(*args, **kwargs):
        print("Pantalla de carga no disponible")

try:
    from reportes_menu import iniciar_reportes
except ImportError as e:
    print(f"Warning: reportes_menu module not found: {e}")
    def iniciar_reportes():
        messagebox.showwarning("Módulo no disponible", "El módulo de reportes no está disponible.")

try:
    from clientes_menu import iniciar_clientes
except ImportError as e:
    print(f"Warning: clientes_menu module not found: {e}")
    def iniciar_clientes():
        messagebox.showwarning("Módulo no disponible", "El módulo de clientes no está disponible.")

try:
    from configuracion_menu import iniciar_configuracion
except ImportError as e:
    print(f"Warning: configuracion_menu module not found: {e}")
    def iniciar_configuracion():
        messagebox.showwarning("Módulo no disponible", "El módulo de configuración no está disponible.")

try:
    from usuarios_menu import iniciar_usuarios
except ImportError as e:
    print(f"Warning: usuarios_menu module not found: {e}")
    def iniciar_usuarios():
        messagebox.showwarning("Módulo no disponible", "El módulo de usuarios no está disponible.")

try:
    from inventario_menu import iniciar_inventario
except ImportError as e:
    print(f"Warning: inventario_menu module not found: {e}")
    def iniciar_inventario():
        messagebox.showwarning("Módulo no disponible", "El módulo de inventario no está disponible.")

# Ruta de la base de datos
base_dir = os.path.dirname(os.path.abspath(__file__))
database_dir = os.path.join(base_dir, '..', 'database')
ruta_db = os.path.join(database_dir, 'ventas.db')

# Verificar si existe la base de datos, si no crear el directorio
if not os.path.exists(database_dir):
    try:
        os.makedirs(database_dir, exist_ok=True)
        print(f"Directorio de base de datos creado: {database_dir}")
    except Exception as e:
        print(f"Error creando directorio de base de datos: {e}")

if not os.path.exists(ruta_db):
    print(f"Advertencia: Base de datos no encontrada en {ruta_db}")

# Diccionario de permisos predefinidos para cada rol
PERMISOS = {
    "administrador": {
        "Ventas": 1,
        "Inventario": 1,
        "Clientes": 1,
        "Reportes": 1,
        "Gastos": 1,
        "Usuarios": 1,
        "Configuración": 1,
        "Códigos de Barras": 1
    },
    "admin": {  # Agregar alias para administrador
        "Ventas": 1,
        "Inventario": 1,
        "Clientes": 1,
        "Reportes": 1,
        "Gastos": 1,
        "Usuarios": 1,
        "Configuración": 1,
        "Códigos de Barras": 1
    },
    "vendedor": {
        "Ventas": 1,
        "Inventario": 1,
        "Clientes": 1,
        "Reportes": 1,
        "Gastos": 0,
        "Usuarios": 0,
        "Configuración": 0,
        "Códigos de Barras": 1
    },
    "gerente": {
        "Ventas": 1,
        "Inventario": 1,
        "Clientes": 1,
        "Reportes": 1,
        "Gastos": 0,
        "Usuarios": 1,
        "Configuración": 1,
        "Códigos de Barras": 1
    }
}

class VmPOSDashboard(tk.Tk):
    """
    Clase principal de la aplicación para el Dashboard de VmPOS.
    Hereda de tk.Tk, haciendo que la instancia de la clase sea la ventana principal.
    """
    def __init__(self, usuario="Admin", datos_usuario=None):
        super().__init__()

        self.usuario = usuario
        self.datos_usuario = datos_usuario or {}
        
        # CORRECCIÓN: Obtener rol primero, luego permisos
        rol_raw = self.datos_usuario.get('permisos', 'vendedor')
        self.rol_usuario = rol_raw.lower() if isinstance(rol_raw, str) else 'vendedor'
        self.rol_usuario_display = self.rol_usuario.capitalize()
        
        # Obtener permisos después de definir el rol
        self.permisos = self._get_user_permissions()
        
        # Variables para estadísticas
        self.stats_widgets = {}
        
        # Variables para gastos temporales
        self.entry_concepto = None
        self.entry_valor = None
        self.tree_gastos = None
        self.label_total = None
        
        self._setup_main_window()
        self._create_header()
        self._create_main_content()
        self._create_footer()
        self._bind_shortcuts()
        
        # Actualizar estadísticas cada 30 segundos
        self._actualizar_estadisticas()
        self.after(30000, self._programa_actualizacion_stats)
        
        # Ocultar la pantalla de carga después de inicializar el dashboard
        if isinstance(self.datos_usuario, dict) and 'ventana_carga' in self.datos_usuario:
            try:
                self.datos_usuario['ventana_carga'].destroy()
            except:
                pass  # Ventana ya destruida

    def _get_user_permissions(self):
        """
        Obtiene los permisos del usuario basados en su rol.
        """
        rol = self.rol_usuario.lower()  # Usar el rol ya procesado
        return PERMISOS.get(rol, PERMISOS['vendedor'])

    def _setup_main_window(self):
        """Configura las propiedades de la ventana principal."""
        try:
            self.title(f"VmPOS - Dashboard • {self.usuario} ({self.rol_usuario_display})")
            self.geometry("1200x700")
            self.resizable(False, False)
            self.configure(bg="#ff9ff3")
            
            # Centrar ventana
            self.update_idletasks()
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            x = (screen_width // 2) - (1200 // 2)
            y = (screen_height // 2) - (700 // 2)
            self.geometry(f"1200x700+{x}+{y}")
        except Exception as e:
            print(f"Error configurando ventana principal: {e}")

    def _create_header(self):
        """Crea y empaqueta el encabezado de la aplicación."""
        try:
            header_frame = tk.Frame(self, bg="#e84393", height=80)
            header_frame.pack(fill="x")
            header_frame.pack_propagate(False)

            # Lado izquierdo del encabezado
            header_left = tk.Frame(header_frame, bg="#e84393")
            header_left.pack(side="left", fill="y", padx=30)
            tk.Label(header_left, text="🌸", font=("Segoe UI Emoji", 28), bg="#e84393", fg="white").pack(side="left", pady=15)
            tk.Label(header_left, text="VmPOS", font=("Segoe UI", 24, "bold"), bg="#e84393", fg="white").pack(side="left", padx=(10, 0), pady=18)
            tk.Label(header_left, text="Centro de Copiado & Papelería", font=("Segoe UI", 12), bg="#e84393", fg="#ffd3e8").pack(side="left", padx=(15, 0), pady=20)

            # Lado derecho del encabezado
            header_right = tk.Frame(header_frame, bg="#e84393")
            header_right.pack(side="right", fill="y", padx=30)
            
            tk.Label(header_right, text=f"👤 {self.usuario}", font=("Segoe UI", 14, "bold"), bg="#e84393", fg="white").pack(anchor="e", pady=(12, 2))
            
            # Fecha y hora en tiempo real
            self.lbl_fecha_hora = tk.Label(header_right, text="", font=("Segoe UI", 10), bg="#e84393", fg="#ffd3e8")
            self.lbl_fecha_hora.pack(anchor="e")
            
            emoji_rol = "👑" if self.rol_usuario in ["admin", "administrador"] else "👩‍💼"
            tk.Label(header_right, text=f"{emoji_rol} {self.rol_usuario_display}", font=("Segoe UI", 10), bg="#e84393", fg="#ffd3e8").pack(anchor="e", pady=(2, 12))
            
            # Actualizar fecha y hora
            self._actualizar_fecha_hora()
        except Exception as e:
            print(f"Error creando header: {e}")

    def _actualizar_fecha_hora(self):
        """Actualiza la fecha y hora en tiempo real."""
        try:
            if hasattr(self, 'lbl_fecha_hora') and self.lbl_fecha_hora.winfo_exists():
                now = datetime.datetime.now()
                fecha_actual = now.strftime("%d/%m/%Y")
                hora_actual = now.strftime("%H:%M:%S")
                self.lbl_fecha_hora.config(text=f"📅 {fecha_actual} • 🕐 {hora_actual}")
                # Programar la siguiente actualización en 1 segundo
                self.after(1000, self._actualizar_fecha_hora)
        except Exception as e:
            print(f"Error actualizando fecha/hora: {e}")

    def _obtener_ganancias_hoy(self):
        """
        Obtiene las ganancias netas del día actual (ventas - gastos).
        """
        try:
            if not os.path.exists(ruta_db):
                return 0
                
            conn = sqlite3.connect(ruta_db)
            cursor = conn.cursor()
            fecha_hoy = datetime.date.today().strftime('%Y-%m-%d')
            
            # 1. Obtener total de ventas del día
            cursor.execute("""
                SELECT SUM(total_venta) 
                FROM ventas 
                WHERE DATE(fecha_venta) = ?
            """, (fecha_hoy,))
            resultado_ventas = cursor.fetchone()
            total_ventas = resultado_ventas[0] if resultado_ventas and resultado_ventas[0] else 0
            
            # 2. Obtener total de gastos del día
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='gastos'
            """)
            tabla_gastos_existe = cursor.fetchone()
            
            total_gastos = 0
            if tabla_gastos_existe:
                fecha_hoy_formato_gasto = datetime.date.today().strftime('%d-%m-%Y')
                cursor.execute("""
                    SELECT SUM(valor) FROM gastos
                    WHERE fecha = ?
                """, (fecha_hoy_formato_gasto,))
                resultado_gastos = cursor.fetchone()
                total_gastos = resultado_gastos[0] if resultado_gastos and resultado_gastos[0] else 0
            
            # 3. Calcular ganancia neta
            ganancia_neta = total_ventas - total_gastos
            conn.close()
            return ganancia_neta
            
        except Exception as e:
            print(f"Error al obtener ganancias de hoy: {e}")
            return 0

    def _obtener_total_productos_inventario(self):
        """Obtiene el total de productos en inventario."""
        try:
            if not os.path.exists(ruta_db):
                return 0
                
            conn = sqlite3.connect(ruta_db)
            cursor = conn.cursor()
            
            # Verificar si la tabla productos existe
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='productos'
            """)
            tabla_existe = cursor.fetchone()
            
            if tabla_existe:
                cursor.execute("SELECT COUNT(*) FROM productos")
                resultado = cursor.fetchone()
                conn.close()
                return resultado[0] if resultado and resultado[0] else 0
            else:
                conn.close()
                return 0
        except Exception as e:
            print(f"Error al obtener total de productos: {e}")
            return 0
            
    def _obtener_clientes_unicos_hoy(self):
        """
        Obtiene el número de clientes únicos que han comprado hoy.
        """
        try:
            if not os.path.exists(ruta_db):
                return 0
                
            conn = sqlite3.connect(ruta_db)
            cursor = conn.cursor()
            fecha_hoy = datetime.date.today().strftime('%Y-%m-%d')
            
            # Verificar si la tabla ventas existe
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='ventas'
            """)
            tabla_existe = cursor.fetchone()
            
            if not tabla_existe:
                conn.close()
                return 0
            
            # Verificar estructura de la tabla ventas
            cursor.execute("PRAGMA table_info(ventas)")
            columnas = cursor.fetchall()
            columnas_nombres = [col[1] for col in columnas]
            
            if 'cliente_id' in columnas_nombres:
                cursor.execute("""
                    SELECT COUNT(DISTINCT cliente_id)
                    FROM ventas
                    WHERE DATE(fecha_venta) = ?
                """, (fecha_hoy,))
            else:
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM ventas
                    WHERE DATE(fecha_venta) = ?
                """, (fecha_hoy,))
            
            resultado = cursor.fetchone()
            conn.close()
            return resultado[0] if resultado and resultado[0] else 0
        except Exception as e:
            print(f"Error al obtener clientes únicos de hoy: {e}")
            return 0

    def _obtener_pedidos_hoy(self):
        """
        Obtiene el número de pedidos realizados hoy.
        """
        try:
            if not os.path.exists(ruta_db):
                return 0
                
            conn = sqlite3.connect(ruta_db)
            cursor = conn.cursor()
            fecha_hoy = datetime.date.today().strftime('%Y-%m-%d')
            
            # Verificar si la tabla ventas existe
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='ventas'
            """)
            tabla_existe = cursor.fetchone()
            
            if tabla_existe:
                cursor.execute("SELECT COUNT(*) FROM ventas WHERE DATE(fecha_venta) = ?", (fecha_hoy,))
                resultado = cursor.fetchone()
                conn.close()
                return resultado[0] if resultado and resultado[0] else 0
            else:
                conn.close()
                return 0
        except Exception as e:
            print(f"Error al obtener pedidos de hoy: {e}")
            return 0

    def _actualizar_estadisticas(self):
        """Actualiza todas las estadísticas del dashboard."""
        try:
            # Obtener datos con manejo de errores individual
            try:
                ganancias_hoy = self._obtener_ganancias_hoy()
            except Exception as e:
                print(f"Error obteniendo ganancias: {e}")
                ganancias_hoy = 0
                
            try:
                total_productos = self._obtener_total_productos_inventario()
            except Exception as e:
                print(f"Error obteniendo productos: {e}")
                total_productos = 0
                
            try:
                clientes_hoy = self._obtener_clientes_unicos_hoy()
            except Exception as e:
                print(f"Error obteniendo clientes: {e}")
                clientes_hoy = 0
                
            try:
                pedidos_hoy = self._obtener_pedidos_hoy()
            except Exception as e:
                print(f"Error obteniendo pedidos: {e}")
                pedidos_hoy = 0
            
            # Actualizar widgets solo si existen y están válidos
            widgets_updates = {
                'ganancias': self._formato_peso(ganancias_hoy),
                'productos': str(total_productos),
                'clientes': str(clientes_hoy),
                'pedidos': str(pedidos_hoy)
            }
            
            for key, value in widgets_updates.items():
                try:
                    if key in self.stats_widgets and self.stats_widgets[key] and self.stats_widgets[key].winfo_exists():
                        self.stats_widgets[key].config(text=value)
                except tk.TclError:
                    # Widget ya no existe
                    pass
                except Exception as e:
                    print(f"Error actualizando widget {key}: {e}")
                
        except Exception as e:
            print(f"Error general al actualizar estadísticas: {e}")

    def _formato_peso(self, valor):
        """Formatea un valor numérico al formato peso colombiano."""
        try:
            return f"${valor:,.0f} COP"
        except (ValueError, TypeError):
            return "$0 COP"

    def _programa_actualizacion_stats(self):
        """Programa la próxima actualización de estadísticas."""
        try:
            if self.winfo_exists():
                self._actualizar_estadisticas()
                self.after(30000, self._programa_actualizacion_stats)
        except tk.TclError:
            # Ventana ya cerrada
            pass

    def _create_main_content(self):
        """Crea y empaqueta el área de contenido principal, incluyendo estadísticas y botones."""
        try:
            main_content = tk.Frame(self, bg="#ffeaa7")
            main_content.pack(fill="both", expand=True, padx=20, pady=20)

            self._create_stats_panel(main_content)
            self._create_buttons_panel(main_content)
            self._create_quick_access_panel(main_content)
            
            # Mostrar información del modo vendedor si aplica
            if self.rol_usuario == "vendedor":
                permisos_info = tk.Frame(main_content, bg="#FFF3E0", bd=1, relief="solid", height=40)
                permisos_info.pack(fill="x", pady=(10, 0))
                permisos_info.pack_propagate(False)
                tk.Label(permisos_info, text="🛍️ MODO VENDEDOR: Acceso limitado a Ventas, Inventario, Clientes y Reportes", 
                         font=("Segoe UI", 10, "bold"), bg="#FFF3E0", fg="#E65100").pack(pady=10)
        except Exception as e:
            print(f"Error creando contenido principal: {e}")

    def _create_stats_panel(self, parent):
        """
        Crea el panel de estadísticas en la parte superior del área de contenido principal.
        """
        try:
            stats_frame = tk.Frame(parent, bg="#ffeaa7")
            stats_frame.pack(fill="x", pady=(0, 20))

            stats = [
                ("💖", "Ganancias Hoy", "ganancias", "#fd79a8"),
                ("🎀", "Productos", "productos", "#74b9ff"),
                ("💎", "Clientes", "clientes", "#a29bfe"),
                ("🌈", "Pedidos", "pedidos", "#55efc4")
            ]

            for i, (icono, titulo, key, color) in enumerate(stats):
                stat_card = tk.Frame(stats_frame, bg="white", bd=2, relief="solid")
                stat_card.pack(side="left", fill="both", expand=True, padx=(0 if i == 0 else 10, 0))

                card_header = tk.Frame(stat_card, bg=color, height=5)
                card_header.pack(fill="x")
                card_content = tk.Frame(stat_card, bg="white")
                card_content.pack(fill="both", expand=True, padx=20, pady=15)
                tk.Label(card_content, text=icono, font=("Segoe UI Emoji", 24), bg="white").pack()
                tk.Label(card_content, text=titulo, font=("Segoe UI", 11), bg="white", fg="#636e72").pack()
                
                # Crear widget de valor y guardarlo en el diccionario
                valor_inicial = "$0 COP" if key == "ganancias" else "0"
                valor_widget = tk.Label(card_content, text=valor_inicial, font=("Segoe UI", 16, "bold"), bg="white", fg="#2d3436")
                valor_widget.pack()
                self.stats_widgets[key] = valor_widget
        except Exception as e:
            print(f"Error creando panel de estadísticas: {e}")

    def _create_buttons_panel(self, parent):
        """Crea el panel principal con botones de operación, gestión y configuración."""
        try:
            buttons_container = tk.Frame(parent, bg="#ffeaa7")
            buttons_container.pack(fill="both", expand=True)

            left_panel = tk.Frame(buttons_container, bg="white", bd=3, relief="solid")
            left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
            tk.Label(left_panel, text="✨ OPERACIONES PRINCIPALES", font=("Segoe UI", 14, "bold"), bg="white", fg="#e84393").pack(pady=20)
            self._crear_boton_moderno(left_panel, "Nueva Venta", "💖", "#fd79a8", lambda: self._accion("Ventas"), "Ventas")
            self._crear_boton_moderno(left_panel, "Gestionar Inventario", "🎀", "#74b9ff", lambda: self._accion("Inventario"), "Inventario")
            self._crear_boton_moderno(left_panel, "Clientes", "💎", "#55efc4", lambda: self._accion("Clientes"), "Clientes")
            
            center_panel = tk.Frame(buttons_container, bg="white", bd=3, relief="solid")
            center_panel.pack(side="left", fill="both", expand=True, padx=5)
            tk.Label(center_panel, text="💫 GESTIÓN", font=("Segoe UI", 14, "bold"), bg="white", fg="#e84393").pack(pady=20)
            self._crear_boton_moderno(center_panel, "Reportes", "🌈", "#fdcb6e", lambda: self._accion("Reportes"), "Reportes")
            self._crear_boton_moderno(center_panel, "Control de Gastos", "🌸", "#ff7675", lambda: self._accion("Gastos"), "Gastos")
            # AGREGAR EL BOTÓN DEL GENERADOR DE CÓDIGOS DE BARRAS
            self._crear_boton_moderno(center_panel, "Códigos de Barras", "🔢", "#e17055", lambda: self._accion("Códigos de Barras"), "Códigos de Barras")

            right_panel = tk.Frame(buttons_container, bg="white", bd=3, relief="solid")
            right_panel.pack(side="right", fill="both", expand=True, padx=(10, 0))
            tk.Label(right_panel, text="🎨 CONFIGURACIÓN", font=("Segoe UI", 14, "bold"), bg="white", fg="#e84393").pack(pady=20)
            self._crear_boton_moderno(right_panel, "Configuración", "✨", "#a29bfe", lambda: self._accion("Configuración"), "Configuración")
            self._crear_boton_moderno(right_panel, "Usuarios", "👸", "#fd79a8", lambda: self._accion("Usuarios"), "Usuarios")
        except Exception as e:
            print(f"Error creando panel de botones: {e}")

    def _create_quick_access_panel(self, parent):
        """Crea el panel de acceso rápido en la parte inferior del área de contenido principal."""
        try:
            quick_access = tk.Frame(parent, bg="#e84393", height=80)
            quick_access.pack(fill="x", pady=(20, 0))
            quick_access.pack_propagate(False)

            tk.Label(quick_access, text="💫 ACCESO RÁPIDO", font=("Segoe UI", 12, "bold"), bg="#e84393", fg="white").pack(side="left", padx=20, pady=25)
            quick_frame = tk.Frame(quick_access, bg="#e84393")
            quick_frame.pack(side="right", padx=20, pady=15)

            quick_buttons = [
                ("🌟", "Nueva Factura", "#fd79a8", "Ventas", lambda: self._accion("Ventas")),
                ("💎", "Consultar Stock", "#74b9ff", "Inventario", lambda: self._accion("Inventario")),
                ("🔢", "Generar Código", "#e17055", "Códigos de Barras", lambda: self._accion("Códigos de Barras")),
                ("🎀", "Backup", "#55efc4", "Configuración", lambda: self._accion("Configuración")),
                ("✨", "Sincronizar", "#fdcb6e", "Configuración", lambda: self._actualizar_estadisticas())
            ]
            
            for icono, texto, color, modulo, comando in quick_buttons:
                tiene_permiso = self.permisos.get(modulo, 0) == 1 if modulo != "Configuración" or texto != "Sincronizar" else True
                color_final = color if tiene_permiso else "#BDBDBD"
                cursor_final = "hand2" if tiene_permiso else "no"

                def _on_click(cmd, has_perm):
                    return lambda: cmd() if has_perm else self._mostrar_alerta_sin_permisos()

                quick_btn = tk.Button(quick_frame, text=f"{icono}\n{texto}",
                                     font=("Segoe UI", 9, "bold"), bg=color_final, fg="white",
                                     bd=0, cursor=cursor_final, relief="flat", width=10, height=2,
                                     command=_on_click(comando, tiene_permiso))
                quick_btn.pack(side="left", padx=5)
        except Exception as e:
            print(f"Error creando panel de acceso rápido: {e}")

    def _create_footer(self):
        """Crea y empaqueta el pie de página de la aplicación."""
        try:
            footer = tk.Frame(self, bg="#e84393", height=50)
            footer.pack(fill="x")
            footer.pack_propagate(False)

            footer_left = tk.Frame(footer, bg="#e84393")
            footer_left.pack(side="left", padx=20, pady=10)
            tk.Label(footer_left, text="📍 Puerto Colombia • 📞 +573215545788", font=("Segoe UI", 10), bg="#e84393", fg="white").pack()

            footer_right = tk.Frame(footer, bg="#e84393")
            footer_right.pack(side="right", padx=20, pady=10)
            tk.Label(footer_right, text="✨ VmPOS v3.1.0 • Sistema Activo 💖", font=("Segoe UI", 10), bg="#e84393", fg="#ffd3e8").pack()
        except Exception as e:
            print(f"Error creando footer: {e}")

    def _bind_shortcuts(self):
        """Vincula los atajos de teclado para un acceso rápido."""
        try:
            self.bind("<KeyPress>", self._shortcuts)
            self.focus_set()
        except Exception as e:
            print(f"Error vinculando shortcuts: {e}")

    def _shortcuts(self, event):
        """Maneja los atajos de teclado."""
        try:
            key = event.keysym.lower()
            if event.state & 4:  # Verifica si Ctrl está presionado
                if key == 'v' and self.permisos.get("Ventas", 0) == 1:
                    self._accion("Ventas")
                elif key == 'i' and self.permisos.get("Inventario", 0) == 1:
                    self._accion("Inventario")
                elif key == 'c' and self.permisos.get("Clientes", 0) == 1:
                    self._accion("Clientes")
                elif key == 'r' and self.permisos.get("Reportes", 0) == 1:
                    self._accion("Reportes")
                elif key == 'b' and self.permisos.get("Códigos de Barras", 0) == 1:
                    self._accion("Códigos de Barras")
            elif key == 'f5':  # F5 para actualizar estadísticas
                self._actualizar_estadisticas()
        except Exception as e:
            print(f"Error en shortcuts: {e}")

    def _mostrar_alerta_sin_permisos(self):
        """Muestra una alerta personalizada cuando un usuario no tiene permisos."""
        try:
            alerta = tk.Toplevel(self)
            alerta.title("🚫 Acceso Denegado")
            alerta.geometry("400x250")
            alerta.configure(bg="#FFCDD2")
            alerta.resizable(False, False)
            alerta.grab_set()

            # Centrar la ventana de alerta
            alerta.update_idletasks()
            x = (alerta.winfo_screenwidth() // 2) - (400 // 2)
            y = (alerta.winfo_screenheight() // 2) - (250 // 2)
            alerta.geometry(f"400x250+{x}+{y}")

            main_frame = tk.Frame(alerta, bg="white", bd=2, relief="solid")
            main_frame.pack(fill="both", expand=True, padx=15, pady=15)
            header_frame = tk.Frame(main_frame, bg="#F44336", height=60)
            header_frame.pack(fill="x")
            header_frame.pack_propagate(False)
            tk.Label(header_frame, text="🚫", font=("Segoe UI Emoji", 24), bg="#F44336", fg="white").pack(pady=15)
            content_frame = tk.Frame(main_frame, bg="white")
            content_frame.pack(expand=True, fill="both", padx=20, pady=20)
            tk.Label(content_frame, text="ACCESO DENEGADO", font=("Segoe UI", 14, "bold"), bg="white", fg="#F44336").pack(pady=(0, 10))
            tk.Label(content_frame, text="No tienes permisos para acceder\na este módulo del sistema.", font=("Segoe UI", 11), bg="white", fg="#424242", justify="center").pack()
            btn_ok = tk.Button(content_frame, text="🔒 Entendido", font=("Segoe UI", 10, "bold"), bg="#F44336", fg="white", bd=0, pady=8, cursor="hand2", command=alerta.destroy, relief="flat", width=15)
            btn_ok.pack(pady=(15, 0))
            alerta.after(3000, alerta.destroy)
        except Exception as e:
            print(f"Error mostrando alerta de permisos: {e}")

    def _crear_boton_moderno(self, parent, texto, icono, color, comando, modulo=None):
        """
        Crea un botón con estilo con verificación de permisos y efectos de hover.
        """
        try:
            tiene_permiso = self.permisos.get(modulo, 0) == 1
            btn_frame = tk.Frame(parent, bg="white")
            btn_frame.pack(fill="x", padx=20, pady=8)
            
            if not tiene_permiso:
                color_final = "#BDBDBD"
                texto_final = f"🔒   {texto}"
                cursor_final = "no"
            else:
                color_final = color
                texto_final = f"{icono}   {texto}"
                cursor_final = "hand2"

            btn = tk.Button(btn_frame, text=texto_final,
                            font=("Segoe UI", 12, "bold"), bg=color_final, fg="white",
                            bd=0, pady=15, cursor=cursor_final,
                            command=lambda: comando() if tiene_permiso else self._mostrar_alerta_sin_permisos(),
                            relief="flat", anchor="w", padx=20)
            btn.pack(fill="x")

            # Efectos de hover solo para botones habilitados
            if tiene_permiso:
                color_hover = {
                    "#fd79a8": "#e84393",
                    "#74b9ff": "#6c5ce7",
                    "#55efc4": "#00b894",
                    "#ff7675": "#e17055",
                    "#a29bfe": "#6c5ce7",
                    "#fdcb6e": "#f39c12",
                    "#e17055": "#d63031"
                }.get(color, "#e84393")

                def on_enter(e):
                    btn.config(bg=color_hover)
                def on_leave(e):
                    btn.config(bg=color_final)

                btn.bind("<Enter>", on_enter)
                btn.bind("<Leave>", on_leave)
        except Exception as e:
            print(f"Error creando botón moderno: {e}")

    def _abrir_ventas(self):
        """Abre el módulo de ventas."""
        try:
            ventas_path = os.path.join(os.path.dirname(__file__), "ventas_menu.py")
            if os.path.exists(ventas_path):
                subprocess.Popen(["python", ventas_path])
            else:
                messagebox.showwarning("⚠️ Archivo no encontrado", f"No se encontró el archivo ventas_menu.py en:\n{ventas_path}")
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudo abrir el módulo de ventas:\n{e}")

    def _abrir_generador_codigo_barras(self):
        """Abre el generador de códigos de barras."""
        # Primero verificar dependencias
        if not self._verificar_dependencias_generador():
            messagebox.showerror("❌ Dependencias Faltantes", 
                               "Faltan librerías necesarias para el generador.\n\n"
                               "Instala PIL/Pillow ejecutando:\n"
                               "pip install Pillow\n\n"
                               "Luego reinicia la aplicación.")
            return
        
        try:
            # Usar la función importada directamente si está disponible
            if GENERADOR_DISPONIBLE and iniciar_generador_barras is not None:
                print("🚀 Iniciando generador de códigos de barras...")
                iniciar_generador_barras(self)
                print("✅ Generador de códigos de barras iniciado correctamente")
            else:
                # Intentar cargar dinámicamente si la importación falló
                self._cargar_generador_dinamicamente()
                
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error detallado: {error_msg}")
            
            # Mensajes de error específicos
            if "PIL" in error_msg or "Pillow" in error_msg:
                messagebox.showerror("❌ Error PIL/Pillow", 
                                   f"Error con la librería de imágenes PIL/Pillow.\n\n"
                                   f"Instala o actualiza Pillow:\n"
                                   f"pip install --upgrade Pillow\n\n"
                                   f"Error técnico: {error_msg}")
            elif "tkinter" in error_msg.lower():
                messagebox.showerror("❌ Error Tkinter", 
                                   f"Error con la interfaz gráfica.\n\n"
                                   f"Error técnico: {error_msg}")
            elif "No module named" in error_msg or "ModuleNotFoundError" in error_msg:
                messagebox.showerror("❌ Módulo No Encontrado", 
                                   f"No se encontró el módulo del generador de códigos.\n\n"
                                   f"Verifica que el archivo 'generador_codigo_barras.py' "
                                   f"esté en la misma carpeta.\n\n"
                                   f"Error técnico: {error_msg}")
            else:
                messagebox.showerror("❌ Error Inesperado", 
                                   f"Ocurrió un error inesperado al abrir el generador.\n\n"
                                   f"Error técnico: {error_msg}\n\n"
                                   f"Intenta:\n"
                                   f"1. Reiniciar la aplicación\n"
                                   f"2. Verificar que todos los archivos estén presentes\n"
                                   f"3. Ejecutar 'pip install Pillow' si no está instalado")

    def _cargar_generador_dinamicamente(self):
        """Carga el generador dinámicamente si la importación inicial falló."""
        try:
            # Buscar el archivo en múltiples ubicaciones posibles
            possible_paths = [
                os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generador_codigo_barras.py'),
                os.path.join(BASE_DIR, 'generador_codigo_barras.py'),
                os.path.join(BASE_DIR, 'interface', 'generador_codigo_barras.py'),
            ]
            
            generador_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    generador_path = path
                    break
            
            if generador_path is None:
                messagebox.showerror("❌ Archivo No Encontrado", 
                                   f"No se encontró el archivo 'generador_codigo_barras.py'\n\n"
                                   f"Ubicaciones buscadas:\n" + "\n".join(possible_paths) + 
                                   f"\n\nVerifica que el archivo esté presente.")
                return
            
            print(f"📁 Cargando generador desde: {generador_path}")
            
            # Cargar el módulo dinámicamente
            spec = importlib.util.spec_from_file_location("generador_codigo_barras", generador_path)
            if spec is None or spec.loader is None:
                raise ImportError("No se pudo crear la especificación del módulo")
                
            generador_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(generador_module)
            
            # Verificar que la función existe en el módulo
            if not hasattr(generador_module, 'iniciar_generador_barras'):
                raise AttributeError("El módulo no contiene la función 'iniciar_generador_barras'")
            
            # Llamar la función iniciar_generador_barras del módulo cargado
            generador_module.iniciar_generador_barras(self)
            print("✅ Generador cargado dinámicamente y ejecutado")
            
        except FileNotFoundError:
            messagebox.showerror("❌ Archivo No Encontrado", 
                               "No se encontró el archivo 'generador_codigo_barras.py'.\n\n"
                               "Verifica que esté en la misma carpeta que este archivo.")
        except ImportError as import_error:
            messagebox.showerror("❌ Error de Importación", 
                               f"Error importando el generador:\n{str(import_error)}\n\n"
                               f"Verifica que:\n"
                               f"• El archivo no tenga errores de sintaxis\n"
                               f"• Todas las dependencias estén instaladas")
        except AttributeError as attr_error:
            messagebox.showerror("❌ Error de Función", 
                               f"Error en la estructura del generador:\n{str(attr_error)}\n\n"
                               f"El archivo debe contener la función 'iniciar_generador_barras'")
        except Exception as load_error:
            messagebox.showerror("❌ Error de Carga", 
                               f"No se pudo cargar el generador de códigos de barras.\n\n"
                               f"Error: {str(load_error)}\n\n"
                               f"Contacta al administrador del sistema si el problema persiste.")

    def _verificar_dependencias_generador(self):
        """Verifica que las dependencias del generador estén instaladas."""
        try:
            # Verificar PIL/Pillow
            from PIL import Image, ImageDraw, ImageFont
            print("✅ PIL/Pillow disponible")
            return True
        except ImportError as e:
            print(f"❌ PIL/Pillow no disponible: {e}")
            return False
        except Exception as e:
            print(f"❌ Error verificando dependencias: {e}")
            return False

    def _abrir_control_gastos(self):
        """Abre el módulo de control de gastos."""
        try:
            # Intentar abrir el módulo de gastos
            gastos_path = os.path.join(os.path.dirname(__file__), "gastos_menu.py")
            
            # Verificar si el archivo existe
            if os.path.exists(gastos_path):
                subprocess.Popen(["python", gastos_path])
                messagebox.showinfo("✅ Control de Gastos", "Abriendo módulo de control de gastos...")
            else:
                # Si no existe, mostrar una ventana temporal
                self._mostrar_ventana_gastos_temporal()
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudo abrir el módulo de gastos:\n{e}")

    def _mostrar_ventana_gastos_temporal(self):
        """Muestra una ventana temporal para el control de gastos."""
        try:
            ventana_gastos = tk.Toplevel(self)
            ventana_gastos.title("🌸 Control de Gastos - Temporal")
            ventana_gastos.geometry("600x400")
            ventana_gastos.configure(bg="#FFF3E0")
            ventana_gastos.transient(self)
            ventana_gastos.grab_set()

            # Centrar ventana
            ventana_gastos.update_idletasks()
            x = (ventana_gastos.winfo_screenwidth() // 2) - (600 // 2)
            y = (ventana_gastos.winfo_screenheight() // 2) - (400 // 2)
            ventana_gastos.geometry(f"600x400+{x}+{y}")

            # Header
            header_frame = tk.Frame(ventana_gastos, bg="#FF5722", height=60)
            header_frame.pack(fill="x")
            header_frame.pack_propagate(False)
            
            tk.Label(header_frame, text="🌸 CONTROL DE GASTOS", 
                    font=("Segoe UI", 16, "bold"), bg="#FF5722", fg="white").pack(pady=18)

            # Contenido principal
            main_frame = tk.Frame(ventana_gastos, bg="#FFF3E0")
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)

            # Formulario para agregar gasto
            form_frame = tk.LabelFrame(main_frame, text="Agregar Nuevo Gasto", 
                                      bg="#FFF3E0", fg="#E65100", font=("Segoe UI", 12, "bold"))
            form_frame.pack(fill="x", pady=10)

            tk.Label(form_frame, text="Concepto:", bg="#FFF3E0", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", padx=10, pady=5)
            self.entry_concepto = tk.Entry(form_frame, font=("Segoe UI", 10), width=30)
            self.entry_concepto.grid(row=0, column=1, padx=10, pady=5)

            tk.Label(form_frame, text="Valor:", bg="#FFF3E0", font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", padx=10, pady=5)
            self.entry_valor = tk.Entry(form_frame, font=("Segoe UI", 10), width=30)
            self.entry_valor.grid(row=1, column=1, padx=10, pady=5)

            tk.Button(form_frame, text="💾 Guardar Gasto", bg="#4CAF50", fg="white", 
                     font=("Segoe UI", 10, "bold"), command=self._guardar_gasto_temporal).grid(row=2, column=0, columnspan=2, pady=15)

            # Lista de gastos del día
            lista_frame = tk.LabelFrame(main_frame, text="Gastos de Hoy", 
                                       bg="#FFF3E0", fg="#E65100", font=("Segoe UI", 12, "bold"))
            lista_frame.pack(fill="both", expand=True, pady=10)

            # Treeview para mostrar gastos
            self.tree_gastos = ttk.Treeview(lista_frame, columns=("Concepto", "Valor", "Hora"), show="headings")
            self.tree_gastos.pack(fill="both", expand=True, padx=10, pady=10)

            self.tree_gastos.heading("Concepto", text="Concepto")
            self.tree_gastos.heading("Valor", text="Valor")
            self.tree_gastos.heading("Hora", text="Hora")

            self.tree_gastos.column("Concepto", width=250)
            self.tree_gastos.column("Valor", width=150)
            self.tree_gastos.column("Hora", width=100)

            # Cargar gastos del día
            self._cargar_gastos_hoy()

            # Total del día
            self.label_total = tk.Label(lista_frame, text="Total gastos hoy: $0 COP", 
                                       bg="#FFF3E0", fg="#E65100", font=("Segoe UI", 12, "bold"))
            self.label_total.pack(pady=10)
        except Exception as e:
            print(f"Error mostrando ventana de gastos temporal: {e}")

    def _guardar_gasto_temporal(self):
        """Guarda un gasto en la base de datos temporal."""
        try:
            if not hasattr(self, 'entry_concepto') or not hasattr(self, 'entry_valor'):
                messagebox.showerror("❌ Error", "Error en el formulario de gastos.")
                return
                
            concepto = self.entry_concepto.get().strip()
            valor_text = self.entry_valor.get().strip()

            if not concepto or not valor_text:
                messagebox.showwarning("⚠️ Campos vacíos", "Por favor, complete todos los campos.")
                return

            try:
                valor = float(valor_text.replace(",", "").replace("$", ""))
                
                # Crear directorio de base de datos si no existe
                if not os.path.exists(os.path.dirname(ruta_db)):
                    os.makedirs(os.path.dirname(ruta_db), exist_ok=True)
                
                # Conectar a la base de datos y crear tabla si no existe
                conn = sqlite3.connect(ruta_db)
                cursor = conn.cursor()
                
                # Crear tabla gastos si no existe
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS gastos (
                        id_gasto INTEGER PRIMARY KEY AUTOINCREMENT,
                        concepto TEXT NOT NULL,
                        valor REAL NOT NULL,
                        fecha TEXT NOT NULL,
                        hora TEXT NOT NULL,
                        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Insertar el gasto
                fecha_hoy = datetime.date.today().strftime('%d-%m-%Y')
                hora_actual = datetime.datetime.now().strftime('%H:%M:%S')
                
                cursor.execute("""
                    INSERT INTO gastos (concepto, valor, fecha, hora)
                    VALUES (?, ?, ?, ?)
                """, (concepto, valor, fecha_hoy, hora_actual))
                
                conn.commit()
                conn.close()

                # Limpiar formulario
                self.entry_concepto.delete(0, tk.END)
                self.entry_valor.delete(0, tk.END)

                # Recargar lista
                self._cargar_gastos_hoy()
                
                # Actualizar estadísticas del dashboard principal
                self._actualizar_estadisticas()

                messagebox.showinfo("✅ Gasto Guardado", f"Gasto guardado exitosamente:\n{concepto} - ${valor:,.0f}")

            except ValueError:
                messagebox.showerror("❌ Error", "El valor debe ser un número válido.")
        except Exception as e:
            messagebox.showerror("❌ Error", f"Error al guardar gasto: {e}")

    def _cargar_gastos_hoy(self):
        """Carga los gastos del día actual."""
        try:
            if not hasattr(self, 'tree_gastos') or not self.tree_gastos:
                return
                
            # Limpiar tree
            for item in self.tree_gastos.get_children():
                self.tree_gastos.delete(item)

            if not os.path.exists(ruta_db):
                if hasattr(self, 'label_total') and self.label_total:
                    self.label_total.config(text="Total gastos hoy: $0 COP")
                return

            conn = sqlite3.connect(ruta_db)
            cursor = conn.cursor()
            
            # Verificar si existe la tabla gastos
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='gastos'
            """)
            
            tabla_existe = cursor.fetchone()
            total_dia = 0
            
            if tabla_existe:
                fecha_hoy = datetime.date.today().strftime('%d-%m-%Y')
                cursor.execute("""
                    SELECT concepto, valor, hora FROM gastos
                    WHERE fecha = ?
                    ORDER BY hora DESC
                """, (fecha_hoy,))
                
                gastos = cursor.fetchall()
                
                for concepto, valor, hora in gastos:
                    self.tree_gastos.insert("", tk.END, values=(concepto, f"${valor:,.0f}", hora))
                    total_dia += valor

            # Verificar que el widget existe antes de actualizarlo
            if hasattr(self, 'label_total') and self.label_total:
                self.label_total.config(text=f"Total gastos hoy: ${total_dia:,.0f} COP")
            
            conn.close()

        except Exception as e:
            print(f"Error al cargar gastos: {e}")

    def _accion(self, nombre):
        """Función centralizada para manejar todas las acciones de los botones."""
        # Verificar permisos aquí como un respaldo
        if self.permisos.get(nombre, 0) == 0:
            self._mostrar_alerta_sin_permisos()
            return

        try:
            # Diccionario para el manejo de acciones - CORREGIDO
            actions = {
                "Ventas": self._abrir_ventas,
                "Inventario": lambda: iniciar_inventario() if 'iniciar_inventario' in globals() else messagebox.showwarning("⚠️ Módulo no disponible", "El módulo de inventario no está disponible."),
                "Clientes": lambda: iniciar_clientes() if 'iniciar_clientes' in globals() else messagebox.showwarning("⚠️ Módulo no disponible", "El módulo de clientes no está disponible."),
                "Reportes": lambda: iniciar_reportes() if 'iniciar_reportes' in globals() else messagebox.showwarning("⚠️ Módulo no disponible", "El módulo de reportes no está disponible."),
                "Configuración": lambda: iniciar_configuracion() if 'iniciar_configuracion' in globals() else messagebox.showwarning("⚠️ Módulo no disponible", "El módulo de configuración no está disponible."),
                "Usuarios": lambda: iniciar_usuarios() if 'iniciar_usuarios' in globals() else messagebox.showwarning("⚠️ Módulo no disponible", "El módulo de usuarios no está disponible."),
                "Gastos": self._abrir_control_gastos,
                "Códigos de Barras": self._abrir_generador_codigo_barras  # ACCIÓN CORREGIDA
            }
            
            action = actions.get(nombre)
            if action:
                # Actualizar estadísticas antes de abrir módulo
                if nombre in ["Ventas", "Inventario", "Gastos"]:
                    self.after(1000, self._actualizar_estadisticas)
                action()
            else:
                messagebox.showwarning("⚠️ Módulo no disponible", f"El módulo {nombre} no está disponible aún.")
                
        except Exception as e:
            messagebox.showerror("❌ Error", f"Error al abrir {nombre}:\n{str(e)}")


# --- Punto de entrada desde el login ---
def iniciar_dashboard(usuario, datos_usuario):
    """
    Función de entrada principal para lanzar el dashboard.
    Esta es la función que se llamaría desde la pantalla de login.
    """
    try:
        app = VmPOSDashboard(usuario=usuario, datos_usuario=datos_usuario)
        app.mainloop()
    except Exception as e:
        print(f"Error iniciando dashboard: {e}")
        messagebox.showerror("Error Fatal", f"Error iniciando el dashboard:\n{e}")


# --- Punto de entrada principal para pruebas independientes ---
if __name__ == "__main__":
    try:
        # Simular una llamada desde la pantalla de login
        # para probar los diferentes roles.
        
        # Usuario Administrador
        mock_admin_data = {'usuario': 'Eduardo', 'permisos': 'admin'}
        print(f"Probando con usuario: {mock_admin_data['usuario']} ({mock_admin_data['permisos']})")
        iniciar_dashboard(mock_admin_data['usuario'], mock_admin_data)

        # # Usuario Vendedor (descomenta para probar)
        # mock_vendedor_data = {'usuario': 'Andres', 'permisos': 'vendedor'}
        # print(f"Probando con usuario: {mock_vendedor_data['usuario']} ({mock_vendedor_data['permisos']})")
        # iniciar_dashboard(mock_vendedor_data['usuario'], mock_vendedor_data)
    except Exception as e:
        print(f"Error fatal en punto de entrada: {e}")
        import traceback
        traceback.print_exc()