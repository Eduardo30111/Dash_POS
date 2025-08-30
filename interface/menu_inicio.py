import tkinter as tk
from tkinter import ttk
import subprocess
import datetime
from tkinter import messagebox
import sqlite3
import os

# Importaciones de los módulos de interfaz
try:
    from pantalla_carga import mostrar_carga
except ImportError:
    print("Warning: pantalla_carga module not found")

try:
    from reportes_menu import iniciar_reportes
except ImportError:
    print("Warning: reportes_menu module not found")

try:
    from clientes_menu import iniciar_clientes
except ImportError:
    print("Warning: clientes_menu module not found")

try:
    from configuracion_menu import iniciar_configuracion
except ImportError:
    print("Warning: configuracion_menu module not found")

try:
    from usuarios_menu import iniciar_usuarios
except ImportError:
    print("Warning: usuarios_menu module not found")

try:
    from inventario_menu import iniciar_inventario
except ImportError:
    print("Warning: inventario_menu module not found")

# Ruta de la base de datos
base_dir = os.path.dirname(os.path.abspath(__file__))
database_dir = os.path.join(base_dir, '..', 'database')
ruta_db = os.path.join(database_dir, 'ventas.db')

# Verificar si existe la base de datos
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
        "Configuración": 1
    },
    "vendedor": {
        "Ventas": 1,
        "Inventario": 1,
        "Clientes": 1,
        "Reportes": 1,
        "Gastos": 0,
        "Usuarios": 0,
        "Configuración": 0
    },

    "gerente": {
        "Ventas": 1,
        "Inventario": 1,
        "Clientes": 1,
        "Reportes": 1,
        "Gastos": 0,
        "Usuarios": 1,
        "Configuración": 1
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
        # Obtener el rol del usuario de los datos de login
        self.rol_usuario = self.datos_usuario.get('permisos', "admin").capitalize()
        self.permisos = self._get_user_permissions()
        
        # Variables para estadísticas
        self.stats_widgets = {}
        
        self._setup_main_window()
        self._create_header()
        self._create_main_content()
        self._create_footer()
        self._bind_shortcuts()
        
        # Actualizar estadísticas cada 30 segundos
        self._actualizar_estadisticas()
        self.after(30000, self._programa_actualizacion_stats)
        
        # Ocultar la pantalla de carga después de inicializar el dashboard
        if 'ventana_carga' in self.datos_usuario:
            self.datos_usuario['ventana_carga'].destroy()

    def _get_user_permissions(self):
        """
        Obtiene los permisos del usuario basados en su rol.
        """
        rol = self.datos_usuario.get('permisos', 'vendedor')
        return PERMISOS.get(rol, PERMISOS['vendedor'])

    def _setup_main_window(self):
        """Configura las propiedades de la ventana principal."""
        self.title(f"VmPOS - Dashboard • {self.usuario} ({self.rol_usuario})")
        self.geometry("1200x700")
        self.resizable(False, False)
        self.configure(bg="#ff9ff3")
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (1200 // 2)
        y = (self.winfo_screenheight() // 2) - (700 // 2)
        self.geometry(f"1200x700+{x}+{y}")

    def _create_header(self):
        """Crea y empaqueta el encabezado de la aplicación."""
        header_frame = tk.Frame(self, bg="#e84393", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)

        # Lado izquierdo del encabezado (logo y título)
        header_left = tk.Frame(header_frame, bg="#e84393")
        header_left.pack(side="left", fill="y", padx=30)
        tk.Label(header_left, text="🌸", font=("Segoe UI Emoji", 28), bg="#e84393", fg="white").pack(side="left", pady=15)
        tk.Label(header_left, text="VmPOS", font=("Segoe UI", 24, "bold"), bg="#e84393", fg="white").pack(side="left", padx=(10, 0), pady=18)
        tk.Label(header_left, text="Centro de Copiado & Papelería", font=("Segoe UI", 12), bg="#e84393", fg="#ffd3e8").pack(side="left", padx=(15, 0), pady=20)

        # Lado derecho del encabezado (información del usuario con hora en vivo)
        header_right = tk.Frame(header_frame, bg="#e84393")
        header_right.pack(side="right", fill="y", padx=30)
        
        # Información del usuario
        emoji_rol = "👑" if self.rol_usuario == "Admin" else "👩‍💼"
        tk.Label(header_right, text=f"👤 {self.usuario}", font=("Segoe UI", 14, "bold"), bg="#e84393", fg="white").pack(anchor="e", pady=(12, 2))
        
        # Fecha y hora en tiempo real
        self.lbl_fecha_hora = tk.Label(header_right, text="", font=("Segoe UI", 10), bg="#e84393", fg="#ffd3e8")
        self.lbl_fecha_hora.pack(anchor="e")
        
        tk.Label(header_right, text=f"{emoji_rol} {self.rol_usuario}", font=("Segoe UI", 10), bg="#e84393", fg="#ffd3e8").pack(anchor="e", pady=(2, 12))
        
        # Actualizar fecha y hora
        self._actualizar_fecha_hora()

    def _actualizar_fecha_hora(self):
        """Actualiza la fecha y hora en tiempo real."""
        now = datetime.datetime.now()
        fecha_actual = now.strftime("%d/%m/%Y")
        hora_actual = now.strftime("%H:%M:%S")
        self.lbl_fecha_hora.config(text=f"📅 {fecha_actual} • 🕐 {hora_actual}")
        # Programar la siguiente actualización en 1 segundo
        self.after(1000, self._actualizar_fecha_hora)

    def _obtener_ganancias_hoy(self):
        """
        Obtiene las ganancias netas del día actual (ventas - gastos).
        """
        try:
            conn = sqlite3.connect(ruta_db)
            cursor = conn.cursor()
            fecha_hoy = datetime.date.today().strftime('%Y-%m-%d')
            
            print(f"Calculando ganancias netas para la fecha: {fecha_hoy}")
            
            # 1. Obtener total de ventas del día
            cursor.execute("""
                SELECT SUM(total_venta) 
                FROM ventas 
                WHERE DATE(fecha_venta) = ?
            """, (fecha_hoy,))
            resultado_ventas = cursor.fetchone()[0]
            total_ventas = resultado_ventas if resultado_ventas else 0
            
            print(f"Total ventas del día: {total_ventas}")
            
            # 2. Obtener total de gastos del día
            # Verificar si la tabla gastos existe
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='gastos'
            """)
            tabla_gastos_existe = cursor.fetchone()
            
            total_gastos = 0
            if tabla_gastos_existe:
                # Los gastos se almacenan con fecha en formato DD-MM-YYYY
                fecha_hoy_formato_gasto = datetime.date.today().strftime('%d-%m-%Y')
                cursor.execute("""
                    SELECT SUM(valor) FROM gastos
                    WHERE fecha = ?
                """, (fecha_hoy_formato_gasto,))
                resultado_gastos = cursor.fetchone()[0]
                total_gastos = resultado_gastos if resultado_gastos else 0
            
            print(f"Total gastos del día: {total_gastos}")
            
            # 3. Calcular ganancia neta
            ganancia_neta = total_ventas - total_gastos
            print(f"Ganancia neta del día: {ganancia_neta}")
            
            conn.close()
            return ganancia_neta
            
        except Exception as e:
            print(f"Error al obtener ganancias de hoy: {e}")
            return 0

    def _obtener_total_productos_inventario(self):
        """Obtiene el total de productos en inventario."""
        try:
            conn = sqlite3.connect(ruta_db)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM productos")
            resultado = cursor.fetchone()[0]
            conn.close()
            return resultado if resultado else 0
        except Exception as e:
            print(f"Error al obtener total de productos: {e}")
            return 0
            
    def _obtener_clientes_unicos_hoy(self):
        """
        Obtiene el número de clientes únicos que han comprado hoy.
        """
        try:
            conn = sqlite3.connect(ruta_db)
            cursor = conn.cursor()
            fecha_hoy = datetime.date.today().strftime('%Y-%m-%d')
            print(f"Buscando clientes únicos para la fecha: {fecha_hoy}")
            
            # Verificar estructura de la tabla ventas
            cursor.execute("PRAGMA table_info(ventas)")
            columnas = cursor.fetchall()
            columnas_nombres = [col[1] for col in columnas]
            
            if 'cliente_id' in columnas_nombres:
                # Si existe columna cliente_id
                cursor.execute("""
                    SELECT COUNT(DISTINCT cliente_id)
                    FROM ventas
                    WHERE DATE(fecha_venta) = ?
                """, (fecha_hoy,))
            else:
                # Si no existe, contar las ventas únicas del día
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM ventas
                    WHERE DATE(fecha_venta) = ?
                """, (fecha_hoy,))
            
            resultado = cursor.fetchone()[0]
            conn.close()
            return resultado if resultado else 0
        except Exception as e:
            print(f"Error al obtener clientes únicos de hoy: {e}")
            return 0

    def _obtener_pedidos_hoy(self):
        """
        Obtiene el número de pedidos realizados hoy.
        """
        try:
            conn = sqlite3.connect(ruta_db)
            cursor = conn.cursor()
            fecha_hoy = datetime.date.today().strftime('%Y-%m-%d')
            print(f"Buscando pedidos totales para la fecha: {fecha_hoy}")
            
            cursor.execute("SELECT COUNT(*) FROM ventas WHERE DATE(fecha_venta) = ?", (fecha_hoy,))
            resultado = cursor.fetchone()[0]
            conn.close()
            return resultado if resultado else 0
        except Exception as e:
            print(f"Error al obtener pedidos de hoy: {e}")
            return 0

    def _actualizar_estadisticas(self):
        """Actualiza todas las estadísticas del dashboard."""
        try:
            # Obtener datos actualizados
            ganancias_hoy = self._obtener_ganancias_hoy()
            total_productos = self._obtener_total_productos_inventario()
            clientes_hoy = self._obtener_clientes_unicos_hoy()
            pedidos_hoy = self._obtener_pedidos_hoy()
            
            # Actualizar widgets si existen
            if 'ganancias' in self.stats_widgets:
                self.stats_widgets['ganancias'].config(text=self._formato_peso(ganancias_hoy))
            if 'productos' in self.stats_widgets:
                self.stats_widgets['productos'].config(text=str(total_productos))
            if 'clientes' in self.stats_widgets:
                self.stats_widgets['clientes'].config(text=str(clientes_hoy))
            if 'pedidos' in self.stats_widgets:
                self.stats_widgets['pedidos'].config(text=str(pedidos_hoy))
                
        except Exception as e:
            print(f"Error al actualizar estadísticas: {e}")

    def _formato_peso(self, valor):
        """Formatea un valor numérico al formato peso colombiano."""
        return f"${valor:,.0f} COP"

    def _programa_actualizacion_stats(self):
        """Programa la próxima actualización de estadísticas."""
        self._actualizar_estadisticas()
        self.after(30000, self._programa_actualizacion_stats)

    def _create_main_content(self,):
        """Crea y empaqueta el área de contenido principal, incluyendo estadísticas y botones."""
        main_content = tk.Frame(self, bg="#ffeaa7")
        main_content.pack(fill="both", expand=True, padx=20, pady=20)

        self._create_stats_panel(main_content)
        self._create_buttons_panel(main_content)
        self._create_quick_access_panel(main_content)
        
        # Mostrar información del modo vendedor si aplica
        if self.rol_usuario == "Vendedor":
            permisos_info = tk.Frame(main_content, bg="#FFF3E0", bd=1, relief="solid", height=40)
            permisos_info.pack(fill="x", pady=(10, 0))
            permisos_info.pack_propagate(False)
            tk.Label(permisos_info, text="🛍️ MODO VENDEDOR: Acceso limitado a Ventas, Inventario, Clientes y Reportes", 
                     font=("Segoe UI", 10, "bold"), bg="#FFF3E0", fg="#E65100").pack(pady=10)

    def _create_stats_panel(self, parent):
        """
        Crea el panel de estadísticas en la parte superior del área de contenido principal.
        """
        stats_frame = tk.Frame(parent, bg="#ffeaa7")
        stats_frame.pack(fill="x", pady=(0, 20))

        stats = [
            ("💖", "Ganancias Hoy", "ganancias", "#fd79a8"), # Ganancias netas (ventas - gastos)
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

    def _create_buttons_panel(self, parent):
        """Crea el panel principal con botones de operación, gestión y configuración."""
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

        right_panel = tk.Frame(buttons_container, bg="white", bd=3, relief="solid")
        right_panel.pack(side="right", fill="both", expand=True, padx=(10, 0))
        tk.Label(right_panel, text="🎨 CONFIGURACIÓN", font=("Segoe UI", 14, "bold"), bg="white", fg="#e84393").pack(pady=20)
        self._crear_boton_moderno(right_panel, "Configuración", "✨", "#a29bfe", lambda: self._accion("Configuración"), "Configuración")
        self._crear_boton_moderno(right_panel, "Usuarios", "👸", "#fd79a8", lambda: self._accion("Usuarios"), "Usuarios")

    def _create_quick_access_panel(self, parent):
        """Crea el panel de acceso rápido en la parte inferior del área de contenido principal."""
        quick_access = tk.Frame(parent, bg="#e84393", height=80)
        quick_access.pack(fill="x", pady=(20, 0))
        quick_access.pack_propagate(False)

        tk.Label(quick_access, text="💫 ACCESO RÁPIDO", font=("Segoe UI", 12, "bold"), bg="#e84393", fg="white").pack(side="left", padx=20, pady=25)
        quick_frame = tk.Frame(quick_access, bg="#e84393")
        quick_frame.pack(side="right", padx=20, pady=15)

        quick_buttons = [
            ("🌟", "Nueva Factura", "#fd79a8", "Ventas", lambda: self._accion("Ventas")),
            ("💎", "Consultar Stock", "#74b9ff", "Inventario", lambda: self._accion("Inventario")),
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

    def _create_footer(self):
        """Crea y empaqueta el pie de página de la aplicación."""
        footer = tk.Frame(self, bg="#e84393", height=50)
        footer.pack(fill="x")
        footer.pack_propagate(False)

        footer_left = tk.Frame(footer, bg="#e84393")
        footer_left.pack(side="left", padx=20, pady=10)
        tk.Label(footer_left, text="📍 Puerto Colombia • 📞 +573215545788", font=("Segoe UI", 10), bg="#e84393", fg="white").pack()

        footer_right = tk.Frame(footer, bg="#e84393")
        footer_right.pack(side="right", padx=20, pady=10)
        tk.Label(footer_right, text="✨ VmPOS v3.1.0 • Sistema Activo 💖", font=("Segoe UI", 10), bg="#e84393", fg="#ffd3e8").pack()

    def _bind_shortcuts(self):
        """Vincula los atajos de teclado para un acceso rápido."""
        self.bind("<KeyPress>", self._shortcuts)
        self.focus_set()

    def _shortcuts(self, event):
        """Maneja los atajos de teclado."""
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
            elif key == 'f5':  # F5 para actualizar estadísticas
                self._actualizar_estadisticas()

    def _mostrar_alerta_sin_permisos(self):
        """Muestra una alerta personalizada cuando un usuario no tiene permisos."""
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

    def _crear_boton_moderno(self, parent, texto, icono, color, comando, modulo=None):
        """
        Crea un botón con estilo con verificación de permisos y efectos de hover.
        """
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
                "#fdcb6e": "#f39c12"
            }.get(color, "#e84393")

            def on_enter(e):
                btn.config(bg=color_hover)
            def on_leave(e):
                btn.config(bg=color_final)

            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)

    def _abrir_ventas(self):
        """Abre el módulo de ventas."""
        try:
            subprocess.Popen(["python", os.path.join(os.path.dirname(__file__), "ventas_menu.py")])
            messagebox.showinfo("✅ Ventas", "Abriendo módulo de ventas...")
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudo abrir el módulo de ventas:\n{e}")

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

    def _guardar_gasto_temporal(self):
        """Guarda un gasto en la base de datos temporal."""
        concepto = self.entry_concepto.get().strip()
        valor_text = self.entry_valor.get().strip()

        if not concepto or not valor_text:
            messagebox.showwarning("⚠️ Campos vacíos", "Por favor, complete todos los campos.")
            return

        try:
            valor = float(valor_text.replace(",", "").replace("$", ""))
            
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
            # Limpiar tree
            for item in self.tree_gastos.get_children():
                self.tree_gastos.delete(item)

            conn = sqlite3.connect(ruta_db)
            cursor = conn.cursor()
            
            # Verificar si existe la tabla gastos
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='gastos'
            """)
            
            if cursor.fetchone():
                fecha_hoy = datetime.date.today().strftime('%d-%m-%Y')
                cursor.execute("""
                    SELECT concepto, valor, hora FROM gastos
                    WHERE fecha = ?
                    ORDER BY hora DESC
                """, (fecha_hoy,))
                
                gastos = cursor.fetchall()
                total_dia = 0
                
                for concepto, valor, hora in gastos:
                    self.tree_gastos.insert("", tk.END, values=(concepto, f"${valor:,.0f}", hora))
                    total_dia += valor

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
                "Inventario": lambda: iniciar_inventario() if 'iniciar_inventario' in globals() else messagebox.showwarning("⚠️ Módulo no disponible", "El módulo de inventario no está disponible."),
                "Clientes": lambda: iniciar_clientes() if 'iniciar_clientes' in globals() else messagebox.showwarning("⚠️ Módulo no disponible", "El módulo de clientes no está disponible."),
                "Reportes": lambda: iniciar_reportes() if 'iniciar_reportes' in globals() else messagebox.showwarning("⚠️ Módulo no disponible", "El módulo de reportes no está disponible."),
                "Configuración": lambda: iniciar_configuracion() if 'iniciar_configuracion' in globals() else messagebox.showwarning("⚠️ Módulo no disponible", "El módulo de configuración no está disponible."),
                "Usuarios": lambda: iniciar_usuarios() if 'iniciar_usuarios' in globals() else messagebox.showwarning("⚠️ Módulo no disponible", "El módulo de usuarios no está disponible."),
                "Gastos": self._abrir_control_gastos
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
    app = VmPOSDashboard(usuario=usuario, datos_usuario=datos_usuario)
    app.mainloop()

# --- Punto de entrada principal para pruebas independientes ---
if __name__ == "__main__":
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