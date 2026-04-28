import tkinter as tk
from tkinter import ttk
import datetime
from tkinter import messagebox
import sqlite3
import importlib.util
import os
import sys
import webbrowser

from paths import ventas_db_path
from fiado_db import ensure_fiado_schema
from layout_responsive import (
    bind_reflow_grid_uniform,
    bind_reflow_pack,
    bind_reflow_pair_header_body,
    centrar_ventana,
    crear_cuerpo_modulo_scroll,
    modulo_scroll_finalizar,
)
from ui_theme import T, F_BODY, F_BODY_B, F_SMALL, F_STAT, F_SUB, FONT

ruta_db = ventas_db_path()

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
    from gastos_menu import iniciar_gastos
except ImportError as e:
    print(f"Warning: gastos_menu module not found: {e}")
    def iniciar_gastos(parent=None):
        messagebox.showwarning("Módulo no disponible", "El módulo de gastos no está disponible.")

try:
    from reportes_menu import iniciar_reportes
except ImportError as e:
    print(f"Warning: reportes_menu module not found: {e}")
    def iniciar_reportes(parent=None):
        messagebox.showwarning("Módulo no disponible", "El módulo de reportes no está disponible.")

try:
    from clientes_menu import iniciar_clientes
except ImportError as e:
    print(f"Warning: clientes_menu module not found: {e}")
    def iniciar_clientes(parent=None):
        messagebox.showwarning("Módulo no disponible", "El módulo de clientes no está disponible.")

try:
    from fiado_menu import iniciar_fiado
except ImportError as e:
    print(f"Warning: fiado_menu module not found: {e}")
    def iniciar_fiado(parent=None):
        messagebox.showwarning("Módulo no disponible", "El módulo de fiados no está disponible.")

try:
    from configuracion_menu import iniciar_configuracion
except ImportError as e:
    print(f"Warning: configuracion_menu module not found: {e}")
    def iniciar_configuracion(parent=None):
        messagebox.showwarning("Módulo no disponible", "El módulo de configuración no está disponible.")

try:
    from usuarios_menu import iniciar_usuarios
except ImportError as e:
    print(f"Warning: usuarios_menu module not found: {e}")
    def iniciar_usuarios(parent=None):
        messagebox.showwarning("Módulo no disponible", "El módulo de usuarios no está disponible.")

try:
    from inventario_menu import iniciar_inventario
except ImportError as e:
    print(f"Warning: inventario_menu module not found: {e}")
    def iniciar_inventario(parent=None):
        messagebox.showwarning("Módulo no disponible", "El módulo de inventario no está disponible.")

database_dir = os.path.dirname(ruta_db)
if not os.path.exists(ruta_db):
    print(f"Advertencia: Base de datos no encontrada en {ruta_db} (se creará al usar el sistema)")

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
        "Códigos de Barras": 1,
        "Fiados": 1,
    },
    "admin": {  # Agregar alias para administrador
        "Ventas": 1,
        "Inventario": 1,
        "Clientes": 1,
        "Reportes": 1,
        "Gastos": 1,
        "Usuarios": 1,
        "Configuración": 1,
        "Códigos de Barras": 1,
        "Fiados": 1,
    },
    "vendedor": {
        "Ventas": 1,
        "Inventario": 1,
        "Clientes": 1,
        "Reportes": 1,
        "Gastos": 0,
        "Usuarios": 0,
        "Configuración": 0,
        "Códigos de Barras": 1,
        "Fiados": 1,
    },
    "gerente": {
        "Ventas": 1,
        "Inventario": 1,
        "Clientes": 1,
        "Reportes": 1,
        "Gastos": 0,
        "Usuarios": 1,
        "Configuración": 1,
        "Códigos de Barras": 1,
        "Fiados": 1,
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
        self.license_limited = bool(self.datos_usuario.get("license_limited"))
        self.license_notice_title = self.datos_usuario.get(
            "license_notice_title", "Tu licencia ha vencido"
        )
        self.license_notice_message = self.datos_usuario.get(
            "license_notice_message",
            "Tu licencia ha vencido. Si quieres renovarla, escríbenos por WhatsApp.",
        )
        self.license_notice_whatsapp = str(
            self.datos_usuario.get("license_notice_whatsapp", "3207716590")
        ).strip()
        if self.license_limited:
            # Modo restringido por licencia vencida: no abrir módulos.
            self.permisos = {k: 0 for k in self.permisos.keys()}
        
        # Variables para estadísticas
        self.stats_widgets = {}
        
        # Variables para gastos temporales
        self.entry_concepto = None
        self.entry_valor = None
        self.tree_gastos = None
        self.label_total = None
        
        self._setup_main_window()
        self._create_header()
        self._create_license_banner()
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
            self.resizable(True, True)
            self.minsize(640, 380)
            self.configure(bg=T.BG_APP)
            self.update_idletasks()
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            w = min(1200, max(800, int(screen_width * 0.88)))
            h = min(800, max(520, int(screen_height * 0.82)))
            centrar_ventana(self, w, h)
        except Exception as e:
            print(f"Error configurando ventana principal: {e}")

    def _create_header(self):
        """Crea y empaqueta el encabezado de la aplicación."""
        try:
            header_frame = tk.Frame(self, bg=T.HEADER_BAR, height=80)
            header_frame.pack(fill="x")
            header_frame.pack_propagate(False)

            header_left = tk.Frame(header_frame, bg=T.HEADER_BAR)
            header_left.pack(side="left", fill="y", padx=30)
            tk.Label(
                header_left,
                text="VmPOS",
                font=(FONT, 22, "bold"),
                bg=T.HEADER_BAR,
                fg=T.WHITE,
            ).pack(side="left", pady=22)
            tk.Label(
                header_left,
                text="  ·  Centro de copiado y papelería",
                font=F_BODY,
                bg=T.HEADER_BAR,
                fg=T.HEADER_TEXT_DIM,
            ).pack(side="left", pady=22, padx=(4, 0))

            header_right = tk.Frame(header_frame, bg=T.HEADER_BAR)
            header_right.pack(side="right", fill="y", padx=30)

            tk.Label(
                header_right,
                text=self.usuario,
                font=(FONT, 12, "bold"),
                bg=T.HEADER_BAR,
                fg=T.WHITE,
            ).pack(anchor="e", pady=(14, 2))

            self.lbl_fecha_hora = tk.Label(
                header_right, text="", font=F_SMALL, bg=T.HEADER_BAR, fg=T.HEADER_TEXT_DIM
            )
            self.lbl_fecha_hora.pack(anchor="e")

            emoji_rol = "●" if self.rol_usuario in ["admin", "administrador"] else "○"
            tk.Label(
                header_right,
                text=f"{emoji_rol}  {self.rol_usuario_display}",
                font=F_SMALL,
                bg=T.HEADER_BAR,
                fg=T.HEADER_TEXT_DIM,
            ).pack(anchor="e", pady=(2, 14))
            
            # Actualizar fecha y hora
            self._actualizar_fecha_hora()
        except Exception as e:
            print(f"Error creando header: {e}")

    def _create_license_banner(self):
        """Muestra aviso superior cuando la licencia está vencida/desactivada."""
        if not self.license_limited:
            return
        try:
            fr = tk.Frame(self, bg=T.WARN, height=44)
            fr.pack(fill="x")
            fr.pack_propagate(False)

            txt = f"{self.license_notice_title}: {self.license_notice_message}"
            tk.Label(
                fr,
                text=txt,
                font=F_BODY_B,
                bg=T.WARN,
                fg=T.WHITE,
                anchor="w",
            ).pack(side="left", padx=12, pady=8, fill="x", expand=True)

            wa_num = "".join(ch for ch in self.license_notice_whatsapp if ch.isdigit())
            if not wa_num.startswith("57"):
                wa_num = f"57{wa_num}"
            wa_msg = "Hola, quiero renovar mi licencia de VmPOS."
            wa_url = f"https://wa.me/{wa_num}?text={wa_msg.replace(' ', '%20')}"
            tk.Button(
                fr,
                text="Renovar por WhatsApp",
                font=F_SMALL,
                bg=T.ACCENT,
                fg=T.WHITE,
                bd=0,
                padx=12,
                pady=6,
                relief="flat",
                cursor="hand2",
                command=lambda: webbrowser.open(wa_url),
            ).pack(side="right", padx=10, pady=6)
        except Exception as e:
            print(f"Error creando banner de licencia: {e}")

    def _actualizar_fecha_hora(self):
        """Actualiza la fecha y hora en tiempo real."""
        try:
            if hasattr(self, 'lbl_fecha_hora') and self.lbl_fecha_hora.winfo_exists():
                now = datetime.datetime.now()
                fecha_actual = now.strftime("%d/%m/%Y")
                hora_actual = now.strftime("%H:%M:%S")
                self.lbl_fecha_hora.config(text=f"{fecha_actual}  ·  {hora_actual}")
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
            ensure_fiado_schema(conn)
            fecha_hoy = datetime.date.today().strftime('%Y-%m-%d')
            
            # 1. Ventas del día al contado (fiado no suma hasta cobrar en el módulo Fiados)
            cursor.execute("""
                SELECT COALESCE(SUM(total_venta), 0)
                FROM ventas
                WHERE DATE(fecha_venta) = ?
                  AND LOWER(COALESCE(tipo_pago, 'contado')) != 'fiado'
            """, (fecha_hoy,))
            resultado_ventas = cursor.fetchone()
            total_ventas = float(resultado_ventas[0] or 0)
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='abonos_fiado'"
            )
            if cursor.fetchone():
                cursor.execute(
                    "SELECT COALESCE(SUM(monto), 0) FROM abonos_fiado WHERE fecha = ?",
                    (fecha_hoy,),
                )
                ra = cursor.fetchone()
                total_ventas += float(ra[0] or 0)
            
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
            wrap = tk.Frame(self, bg=T.BG_APP)
            wrap.pack(fill="both", expand=True, padx=20, pady=20)
            main_content = crear_cuerpo_modulo_scroll(wrap, bg=T.BG_APP)

            self._create_stats_panel(main_content)
            self._create_buttons_panel(main_content)
            self._create_quick_access_panel(main_content)

            # Mostrar información del modo vendedor si aplica
            if self.rol_usuario == "vendedor":
                permisos_info = tk.Frame(main_content, bg=T.WARN_BG, highlightbackground=T.BORDER, highlightthickness=1, height=40)
                permisos_info.pack(fill="x", pady=(10, 0))
                permisos_info.pack_propagate(False)
                tk.Label(permisos_info, text="Perfil: vendedor — acceso limitado a módulos según permisos",
                         font=F_SMALL, bg=T.WARN_BG, fg=T.WARN).pack(pady=10)

            modulo_scroll_finalizar(main_content)
        except Exception as e:
            print(f"Error creando contenido principal: {e}")

    def _create_stats_panel(self, parent):
        """
        Crea el panel de estadísticas en la parte superior del área de contenido principal.
        """
        try:
            stats_frame = tk.Frame(parent, bg=T.BG_APP)
            stats_frame.pack(fill="x", pady=(0, 20))

            stats = [
                ("💰 Ingresos netos hoy", "ganancias", T.STAT_1),
                ("📦 Productos en inventario", "productos", T.STAT_2),
                ("👥 Movimientos hoy (clientes)", "clientes", T.STAT_3),
                ("🧾 Ventas hoy (pedidos)", "pedidos", T.STAT_4),
            ]

            pads_w = ((0, 10), (10, 10), (10, 10), (10, 0))
            lista_tarjetas = []
            for i, (titulo, key, color) in enumerate(stats):
                stat_card = tk.Frame(stats_frame, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
                lista_tarjetas.append(stat_card)

                card_header = tk.Frame(stat_card, bg=color, height=4)
                card_header.pack(fill="x")
                card_content = tk.Frame(stat_card, bg=T.BG_CARD)
                card_content.pack(fill="both", expand=True, padx=20, pady=15)
                tk.Label(card_content, text=titulo, font=F_SMALL, bg=T.BG_CARD, fg=T.TEXT_MUTED).pack(anchor="w")

                # Crear widget de valor y guardarlo en el diccionario
                valor_inicial = "$0 COP" if key == "ganancias" else "0"
                valor_widget = tk.Label(card_content, text=valor_inicial, font=F_STAT, bg=T.BG_CARD, fg=T.TEXT)
                valor_widget.pack()
                self.stats_widgets[key] = valor_widget

            bind_reflow_pack(
                stats_frame,
                [
                    (
                        lista_tarjetas[i],
                        {"side": tk.LEFT, "fill": tk.BOTH, "expand": True, "padx": pads_w[i]},
                        {"fill": tk.X, "pady": (0, 10)},
                    )
                    for i in range(len(lista_tarjetas))
                ],
                umbral=880,
                debounce_ms=80,
            )
        except Exception as e:
            print(f"Error creando panel de estadísticas: {e}")

    def _create_buttons_panel(self, parent):
        """Crea el panel principal con botones de operación, gestión y configuración."""
        try:
            buttons_container = tk.Frame(parent, bg=T.BG_APP)
            buttons_container.pack(fill="both", expand=True)

            left_panel = tk.Frame(buttons_container, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
            tk.Label(left_panel, text="🏪  Operaciones", font=F_SUB, bg=T.BG_CARD, fg=T.TEXT).pack(anchor="w", padx=20, pady=(20, 8))
            self._crear_boton_moderno(left_panel, "Nueva venta", "🧾", T.STAT_1, lambda: self._accion("Ventas"), "Ventas")
            self._crear_boton_moderno(left_panel, "Inventario", "📦", T.STAT_2, lambda: self._accion("Inventario"), "Inventario")
            self._crear_boton_moderno(left_panel, "Clientes", "👥", T.STAT_3, lambda: self._accion("Clientes"), "Clientes")

            center_panel = tk.Frame(buttons_container, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
            tk.Label(center_panel, text="📊  Gestión", font=F_SUB, bg=T.BG_CARD, fg=T.TEXT).pack(anchor="w", padx=20, pady=(20, 8))
            self._crear_boton_moderno(center_panel, "Reportes", "📈", T.STAT_4, lambda: self._accion("Reportes"), "Reportes")
            self._crear_boton_moderno(center_panel, "Gastos", "💸", T.WARN, lambda: self._accion("Gastos"), "Gastos")
            self._crear_boton_moderno(center_panel, "Códigos de barras", "🏷️", T.POS_MUTED, lambda: self._accion("Códigos de Barras"), "Códigos de Barras")
            self._crear_boton_moderno(center_panel, "Fiados", "📒", T.ACCENT, lambda: self._accion("Fiados"), "Fiados")

            right_panel = tk.Frame(buttons_container, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
            tk.Label(right_panel, text="🛡️  Administración", font=F_SUB, bg=T.BG_CARD, fg=T.TEXT).pack(anchor="w", padx=20, pady=(20, 8))
            self._crear_boton_moderno(right_panel, "Configuración", "⚙️", T.STAT_2, lambda: self._accion("Configuración"), "Configuración")
            self._crear_boton_moderno(right_panel, "Usuarios", "👤", T.STAT_1, lambda: self._accion("Usuarios"), "Usuarios")

            bind_reflow_pack(
                buttons_container,
                [
                    (
                        left_panel,
                        {"side": tk.LEFT, "fill": tk.BOTH, "expand": True, "padx": (0, 10)},
                        {"fill": tk.X, "pady": (0, 10)},
                    ),
                    (
                        center_panel,
                        {"side": tk.LEFT, "fill": tk.BOTH, "expand": True, "padx": 10},
                        {"fill": tk.X, "pady": (0, 10)},
                    ),
                    (
                        right_panel,
                        {"side": tk.LEFT, "fill": tk.BOTH, "expand": True, "padx": (10, 0)},
                        {"fill": tk.X, "pady": (0, 10)},
                    ),
                ],
                umbral=960,
                debounce_ms=80,
            )
        except Exception as e:
            print(f"Error creando panel de botones: {e}")

    def _create_quick_access_panel(self, parent):
        """Crea el panel de acceso rápido en la parte inferior del área de contenido principal."""
        try:
            quick_access = tk.Frame(parent, bg=T.HEADER_BAR)
            quick_access.pack(fill="x", pady=(20, 0))

            qa_label = tk.Label(
                quick_access,
                text="✨  Accesos rápidos",
                font=F_BODY_B,
                bg=T.HEADER_BAR,
                fg=T.WHITE,
            )
            quick_frame = tk.Frame(quick_access, bg=T.HEADER_BAR)

            quick_buttons = [
                ("🧾  Nueva factura", T.STAT_1, "Ventas", lambda: self._accion("Ventas")),
                ("📦  Stock", T.STAT_2, "Inventario", lambda: self._accion("Inventario")),
                ("🏷️  Códigos", T.STAT_4, "Códigos de Barras", lambda: self._accion("Códigos de Barras")),
                ("💾  Respaldo", T.STAT_3, "Configuración", lambda: self._accion("Configuración")),
                ("🔄  Actualizar", T.ACCENT, "Configuración", lambda: self._actualizar_estadisticas()),
            ]

            quick_btn_widgets = []
            for texto, color, modulo, comando in quick_buttons:
                tiene_permiso = (
                    self.permisos.get(modulo, 0) == 1 if modulo != "Configuración" or texto != "Actualizar" else True
                )
                color_final = color if tiene_permiso else T.DIVIDER
                cursor_final = "hand2" if tiene_permiso else "no"

                def _on_click(cmd, has_perm):
                    return lambda: cmd() if has_perm else self._mostrar_alerta_sin_permisos()

                quick_btn = tk.Button(
                    quick_frame,
                    text=texto,
                    font=F_SMALL,
                    bg=color_final,
                    fg=T.WHITE,
                    bd=0,
                    cursor=cursor_final,
                    relief="flat",
                    padx=10,
                    pady=6,
                    command=_on_click(comando, tiene_permiso),
                )
                quick_btn_widgets.append(quick_btn)

            bind_reflow_pair_header_body(quick_access, qa_label, quick_frame, umbral=760, debounce_ms=80)
            # Siempre en filas (2-3 columnas) para evitar columna vertical de botones.
            bind_reflow_grid_uniform(
                quick_frame,
                quick_btn_widgets,
                columnas_cuando_anchas=3,
                umbral=420,
                debounce_ms=80,
                pad_exterior=4,
            )
        except Exception as e:
            print(f"Error creando panel de acceso rápido: {e}")

    def _create_footer(self):
        """Crea y empaqueta el pie de página de la aplicación."""
        try:
            footer = tk.Frame(self, bg=T.FOOTER, height=48)
            footer.pack(fill="x")
            footer.pack_propagate(False)

            footer_left = tk.Frame(footer, bg=T.FOOTER)
            footer_left.pack(side="left", padx=20, pady=12)
            tk.Label(footer_left, text="Puerto Colombia  ·  +57 321 554 5788", font=F_SMALL, bg=T.FOOTER, fg=T.HEADER_TEXT_DIM).pack()

            footer_right = tk.Frame(footer, bg=T.FOOTER)
            footer_right.pack(side="right", padx=20, pady=12)
            tk.Label(footer_right, text="VmPOS v3.1", font=F_SMALL, bg=T.FOOTER, fg=T.HEADER_TEXT_DIM).pack()
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
            alerta.title("Acceso denegado")
            alerta.configure(bg=T.DANGER_BG)
            alerta.resizable(False, False)
            alerta.grab_set()
            centrar_ventana(alerta, 400, 250)

            main_frame = tk.Frame(alerta, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
            main_frame.pack(fill="both", expand=True, padx=16, pady=16)
            header_frame = tk.Frame(main_frame, bg=T.DANGER, height=48)
            header_frame.pack(fill="x")
            header_frame.pack_propagate(False)
            tk.Label(header_frame, text="Acceso denegado", font=F_BODY_B, bg=T.DANGER, fg=T.WHITE).pack(pady=12)
            content_frame = tk.Frame(main_frame, bg=T.BG_CARD)
            content_frame.pack(expand=True, fill="both", padx=20, pady=20)
            if self.license_limited:
                texto_alerta = (
                    "Tu licencia ha vencido.\n\n"
                    "Los módulos están desactivados hasta renovar la licencia."
                )
            else:
                texto_alerta = "No tiene permisos para este módulo."
            tk.Label(
                content_frame,
                text=texto_alerta,
                font=F_BODY,
                bg=T.BG_CARD,
                fg=T.TEXT,
                justify="center",
            ).pack()
            btn_ok = tk.Button(content_frame, text="Cerrar", font=F_BODY_B, bg=T.DANGER, fg=T.WHITE, bd=0, pady=8, cursor="hand2", command=alerta.destroy, relief="flat", width=12)
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
            btn_frame = tk.Frame(parent, bg=T.BG_CARD)
            btn_frame.pack(fill="x", padx=20, pady=6)
            
            if not tiene_permiso:
                color_final = T.DIVIDER
                texto_final = f"{texto}  (sin permiso)"
                cursor_final = "no"
            else:
                color_final = color
                texto_final = f"{icono}  {texto}"
                cursor_final = "hand2"

            btn = tk.Button(
                btn_frame,
                text=texto_final,
                font=F_BODY_B,
                bg=color_final,
                fg=T.WHITE,
                bd=0,
                pady=12,
                cursor=cursor_final,
                command=lambda: comando() if tiene_permiso else self._mostrar_alerta_sin_permisos(),
                relief="flat",
                anchor="w",
                padx=16,
                activebackground=color_final,
                activeforeground=T.WHITE,
            )
            btn.pack(fill="x")

            if tiene_permiso:
                color_hover = {
                    T.STAT_1: "#0284c7",
                    T.STAT_2: "#6d28d9",
                    T.STAT_3: "#047857",
                    T.STAT_4: "#d97706",
                    T.ACCENT: T.ACCENT_HOVER,
                    T.WARN: "#b45309",
                    T.POS_MUTED: "#334155",
                }.get(color, T.ACCENT_HOVER)

                def on_enter(e, ch=color_hover):
                    btn.config(bg=ch)

                def on_leave(e, cf=color_final):
                    btn.config(bg=cf)

                btn.bind("<Enter>", on_enter)
                btn.bind("<Leave>", on_leave)
        except Exception as e:
            print(f"Error creando botón moderno: {e}")


    def _abrir_ventas(self):
        from navegacion_ventanas import abrir_modulo_con_menu_oculto, preparar_ventana_modulo
        def abrir(db):
            import ventas_menu
            w = tk.Toplevel(db)
            cuerpo = preparar_ventana_modulo(w, db)
            ventas_menu.App(cuerpo, w)
        try:
            abrir_modulo_con_menu_oculto(self, abrir)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el módulo de ventas:\n{e}")

    def _abrir_generador_codigo_barras(self):
        """Abre el generador de códigos de barras como ventana única con retorno al menú."""
        if not self._verificar_dependencias_generador():
            messagebox.showerror(
                "Dependencias faltantes",
                "Faltan librerías para el generador.\n\nInstala Pillow:\npip install Pillow",
            )
            return
        from navegacion_ventanas import abrir_modulo_con_menu_oculto

        def abrir(db):
            if GENERADOR_DISPONIBLE and iniciar_generador_barras is not None:
                iniciar_generador_barras(db)
            else:
                self._cargar_generador_dinamicamente()

        try:
            abrir_modulo_con_menu_oculto(self, abrir)
        except Exception as e:
            error_msg = str(e)
            if "PIL" in error_msg or "Pillow" in error_msg:
                messagebox.showerror(
                    "Error PIL/Pillow",
                    f"Error con Pillow.\n\npip install --upgrade Pillow\n\nDetalle: {error_msg}",
                )
            elif "tkinter" in error_msg.lower():
                messagebox.showerror("Error de interfaz", f"Error técnico: {error_msg}")
            elif "No module named" in error_msg or "ModuleNotFoundError" in error_msg:
                messagebox.showerror("Módulo no encontrado", f"Detalle: {error_msg}")
            else:
                messagebox.showerror("Error", f"No se pudo abrir el generador:\n{error_msg}")

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

    def _abrir_con_retorno(self, abrir_modulo_fn):
        """Abre un módulo (recibe el dashboard como padre), ocultando el menú hasta volver o cerrar."""
        from navegacion_ventanas import abrir_modulo_con_menu_oculto
        try:
            abrir_modulo_con_menu_oculto(self, abrir_modulo_fn)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el módulo:\n{e}")

    def _abrir_control_gastos(self):
        """Abre el módulo de control de gastos (misma lógica de ventana única + volver al menú)."""
        from navegacion_ventanas import abrir_modulo_con_menu_oculto
        try:
            abrir_modulo_con_menu_oculto(self, lambda db: iniciar_gastos(db))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el módulo de gastos:\n{e}")

    def _mostrar_ventana_gastos_temporal(self):
        """Muestra una ventana temporal para el control de gastos."""
        try:
            ventana_gastos = tk.Toplevel(self)
            ventana_gastos.title("Gastos (temporal)")
            ventana_gastos.configure(bg=T.BG_APP)
            ventana_gastos.transient(self)
            ventana_gastos.grab_set()
            centrar_ventana(ventana_gastos, 600, 400)

            header_frame = tk.Frame(ventana_gastos, bg=T.HEADER_BAR, height=56)
            header_frame.pack(fill="x")
            header_frame.pack_propagate(False)
            tk.Label(header_frame, text="Registro de gastos", font=F_SUB, bg=T.HEADER_BAR, fg=T.WHITE).pack(pady=16)

            main_frame = tk.Frame(ventana_gastos, bg=T.BG_APP)
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)

            form_frame = tk.LabelFrame(
                main_frame, text="Nuevo gasto", bg=T.BG_CARD, fg=T.TEXT, font=(FONT, 11, "bold")
            )
            form_frame.pack(fill="x", pady=10)

            tk.Label(form_frame, text="Concepto:", bg=T.BG_CARD, font=F_BODY, fg=T.TEXT_MUTED).grid(row=0, column=0, sticky="w", padx=10, pady=5)
            self.entry_concepto = tk.Entry(form_frame, font=F_BODY, width=30)
            self.entry_concepto.grid(row=0, column=1, padx=10, pady=5)

            tk.Label(form_frame, text="Valor:", bg=T.BG_CARD, font=F_BODY, fg=T.TEXT_MUTED).grid(row=1, column=0, sticky="w", padx=10, pady=5)
            self.entry_valor = tk.Entry(form_frame, font=F_BODY, width=30)
            self.entry_valor.grid(row=1, column=1, padx=10, pady=5)

            tk.Button(
                form_frame,
                text="Guardar",
                bg=T.SUCCESS,
                fg=T.WHITE,
                font=F_BODY_B,
                command=self._guardar_gasto_temporal,
            ).grid(row=2, column=0, columnspan=2, pady=15)

            lista_frame = tk.LabelFrame(
                main_frame, text="Gastos de hoy", bg=T.BG_CARD, fg=T.TEXT, font=(FONT, 11, "bold")
            )
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
            self.label_total = tk.Label(
                lista_frame,
                text="Total gastos hoy: $0 COP",
                bg=T.BG_CARD,
                fg=T.TEXT,
                font=F_BODY_B,
            )
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
            # Diccionario para el manejo de acciones 
            actions = {
                "Ventas": self._abrir_ventas,
                "Inventario": lambda: self._abrir_con_retorno(lambda p: iniciar_inventario(p)) if 'iniciar_inventario' in globals() else messagebox.showwarning("Módulo no disponible", "El módulo de inventario no está disponible."),
                "Clientes": lambda: self._abrir_con_retorno(lambda p: iniciar_clientes(p)) if 'iniciar_clientes' in globals() else messagebox.showwarning("Módulo no disponible", "El módulo de clientes no está disponible."),
                "Fiados": lambda: self._abrir_con_retorno(lambda p: iniciar_fiado(p)) if 'iniciar_fiado' in globals() else messagebox.showwarning("Módulo no disponible", "El módulo de fiados no está disponible."),
                "Reportes": lambda: self._abrir_con_retorno(lambda p: iniciar_reportes(p)) if 'iniciar_reportes' in globals() else messagebox.showwarning("Módulo no disponible", "El módulo de reportes no está disponible."),
                "Configuración": lambda: self._abrir_con_retorno(lambda p: iniciar_configuracion(p)) if 'iniciar_configuracion' in globals() else messagebox.showwarning("Módulo no disponible", "El módulo de configuración no está disponible."),
                "Usuarios": lambda: self._abrir_con_retorno(lambda p: iniciar_usuarios(p)) if 'iniciar_usuarios' in globals() else messagebox.showwarning("Módulo no disponible", "El módulo de usuarios no está disponible."),
                "Gastos": self._abrir_control_gastos,
                "Códigos de Barras": self._abrir_generador_codigo_barras
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