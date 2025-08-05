import tkinter as tk
from tkinter import ttk
import subprocess
import datetime
from tkinter import messagebox

# Note: The imported modules below are assumed to exist in your project.
# You will need to make sure they are in the same directory or on the Python path.
# from reportes_menu import iniciar_reportes
# from clientes_menu import iniciar_clientes
# from configuracion_menu import iniciar_configuracion
# from gastos_menu import iniciar_gastos
# from usuarios_menu import iniciar_usuarios
from pantalla_carga import mostrar_carga
# from usuarios_db import obtener_permisos_por_usuario # This module is not available

# Diccionario de permisos predefinidos para cada rol.
# Esto reemplaza la llamada a 'obtener_permisos_por_usuario' que no estaba disponible.
PERMISOS = {
    "admin": {
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
    }
}

class VmPOSDashboard(tk.Tk):
    """
    Main application class for the VmPOS Dashboard.
    It inherits from tk.Tk, making the class instance the main window.
    """
    def __init__(self, usuario="Admin", datos_usuario=None):
        super().__init__()

        self.usuario = usuario
        self.datos_usuario = datos_usuario
        # Corregido: Se usa la clave 'permisos' del diccionario de login.
        self.rol_usuario = self.datos_usuario.get('permisos', "admin").capitalize()
        self.permisos = self._get_user_permissions()
        
        self._setup_main_window()
        self._create_header()
        self._create_main_content()
        self._create_footer()
        self._bind_shortcuts()
        
        # Ocultar la pantalla de carga después de inicializar el dashboard
        if 'ventana_carga' in self.datos_usuario:
            self.datos_usuario['ventana_carga'].destroy()

    def _get_user_permissions(self):
        """
        Retrieves user permissions based on the user's role.
        """
        # Corregido: Se obtiene el rol del usuario y se buscan los permisos en el diccionario predefinido.
        rol = self.datos_usuario.get('permisos', 'vendedor')
        return PERMISOS.get(rol, PERMISOS['vendedor'])

    def _setup_main_window(self):
        """Configures the main window properties."""
        self.title(f"VmPOS - Dashboard • {self.usuario} ({self.rol_usuario})")
        self.geometry("1200x700")
        self.resizable(False, False)
        self.configure(bg="#ff9ff3")
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (1200 // 2)
        y = (self.winfo_screenheight() // 2) - (700 // 2)
        self.geometry(f"1200x700+{x}+{y}")

    def _create_header(self):
        """Creates and packs the application header."""
        header_frame = tk.Frame(self, bg="#e84393", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)

        # Left side of header (logo and title)
        header_left = tk.Frame(header_frame, bg="#e84393")
        header_left.pack(side="left", fill="y", padx=30)
        tk.Label(header_left, text="🌸", font=("Segoe UI Emoji", 28), bg="#e84393", fg="white").pack(side="left", pady=15)
        tk.Label(header_left, text="VmPOS", font=("Segoe UI", 24, "bold"), bg="#e84393", fg="white").pack(side="left", padx=(10, 0), pady=18)
        tk.Label(header_left, text="Centro de Copiado & Papelería", font=("Segoe UI", 12), bg="#e84393", fg="#ffd3e8").pack(side="left", padx=(15, 0), pady=20)

        # Right side of header (user info)
        header_right = tk.Frame(header_frame, bg="#e84393")
        header_right.pack(side="right", fill="y", padx=30)
        now = datetime.datetime.now()
        fecha_actual = now.strftime("%d/%m/%Y")
        hora_actual = now.strftime("%H:%M")
        # Corregido: Se usa el rol del usuario para el emoji
        emoji_rol = "👑" if self.rol_usuario == "Admin" else "👩‍💼"

        tk.Label(header_right, text=f"👤 {self.usuario}", font=("Segoe UI", 14, "bold"), bg="#e84393", fg="white").pack(anchor="e", pady=(12, 2))
        tk.Label(header_right, text=f"📅 {fecha_actual} • 🕐 {hora_actual}", font=("Segoe UI", 10), bg="#e84393", fg="#ffd3e8").pack(anchor="e")
        tk.Label(header_right, text=f"{emoji_rol} {self.rol_usuario}", font=("Segoe UI", 10), bg="#e84393", fg="#ffd3e8").pack(anchor="e", pady=(2, 12))

    def _create_main_content(self,):
        """Creates and packs the main content area, including stats and buttons."""
        main_content = tk.Frame(self, bg="#ffeaa7")
        main_content.pack(fill="both", expand=True, padx=20, pady=20)

        self._create_stats_panel(main_content)
        self._create_buttons_panel(main_content)
        self._create_quick_access_panel(main_content)
        
        # Display seller mode info if applicable
        if self.rol_usuario == "Vendedor":
            permisos_info = tk.Frame(main_content, bg="#FFF3E0", bd=1, relief="solid", height=40)
            permisos_info.pack(fill="x", pady=(10, 0))
            permisos_info.pack_propagate(False)
            tk.Label(permisos_info, text="🛍️ MODO VENDEDOR: Acceso limitado a Ventas, Inventario, Clientes y Reportes", 
                     font=("Segoe UI", 10, "bold"), bg="#FFF3E0", fg="#E65100").pack(pady=10)

    def _create_stats_panel(self, parent):
        """
        Creates the statistics panel at the top of the main content area.
        Values have been set to zero as requested.
        """
        stats_frame = tk.Frame(parent, bg="#ffeaa7")
        stats_frame.pack(fill="x", pady=(0, 20))

        stats = [
            ("💖", "Ventas Hoy", "$0", "#fd79a8"),
            ("🎀", "Productos", "0", "#74b9ff"),
            ("💎", "Clientes", "0", "#a29bfe"),
            ("🌈", "Pedidos", "0", "#55efc4")
        ]

        for i, (icono, titulo, valor, color) in enumerate(stats):
            stat_card = tk.Frame(stats_frame, bg="white", bd=2, relief="solid")
            stat_card.pack(side="left", fill="both", expand=True, padx=(0 if i == 0 else 10, 0))

            card_header = tk.Frame(stat_card, bg=color, height=5)
            card_header.pack(fill="x")
            card_content = tk.Frame(stat_card, bg="white")
            card_content.pack(fill="both", expand=True, padx=20, pady=15)
            tk.Label(card_content, text=icono, font=("Segoe UI Emoji", 24), bg="white").pack()
            tk.Label(card_content, text=titulo, font=("Segoe UI", 11), bg="white", fg="#636e72").pack()
            tk.Label(card_content, text=valor, font=("Segoe UI", 16, "bold"), bg="white", fg="#2d3436").pack()

    def _create_buttons_panel(self, parent):
        """Creates the main panel with operational, management, and configuration buttons."""
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
        """Creates the quick access panel at the bottom of the main content area."""
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
            ("✨", "Sincronizar", "#fdcb6e", "Configuración", lambda: self._accion("Configuración"))
        ]
        
        for icono, texto, color, modulo, comando in quick_buttons:
            tiene_permiso = self.permisos.get(modulo, 0) == 1
            color_final = color if tiene_permiso else "#BDBDBD"
            cursor_final = "hand2" if tiene_permiso else "no"

            def _on_click(cmd, has_perm):
                return lambda: cmd() if has_perm else self._mostrar_alerta_sin_permisos()

            quick_btn = tk.Button(quick_frame, text=f"{icono}\n{texto}",
                                 font=("Segoe UI", 9, "bold"), bg=color_final, fg="white",
                                 bd=0, cursor=cursor_final, relief="flat", width=10, height=2,
                                 command=_on_click(comando, tiene_permiso))
            quick_btn.pack(side="left", padx=5)

    def _create_footer(self,):
        """Creates and packs the application footer."""
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
        """Binds keyboard shortcuts for quick access."""
        self.bind("<KeyPress>", self._shortcuts)
        self.focus_set()

    def _shortcuts(self, event):
        """Handles keyboard shortcuts."""
        key = event.keysym.lower()
        if event.state & 4:  # Check if Ctrl is pressed
            if key == 'v' and self.permisos.get("Ventas", 0) == 1:
                self._accion("Ventas")
            elif key == 'i' and self.permisos.get("Inventario", 0) == 1:
                self._accion("Inventario")
            elif key == 'c' and self.permisos.get("Clientes", 0) == 1:
                self._accion("Clientes")
            elif key == 'r' and self.permisos.get("Reportes", 0) == 1:
                self._accion("Reportes")

    def _mostrar_alerta_sin_permisos(self):
        """Displays a custom alert when a user lacks permissions."""
        alerta = tk.Toplevel(self)
        alerta.title("🚫 Acceso Denegado")
        alerta.geometry("400x250")
        alerta.configure(bg="#FFCDD2")
        alerta.resizable(False, False)
        alerta.grab_set()

        # Center the alert window
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
        Creates a stylish button with permission checks and hover effects.
        Prefixed with underscore to indicate it's an internal helper method.
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

        # Hover effects only for enabled buttons
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

    def _accion(self, nombre):
        """Centralized function to handle all button actions."""
        # Check permissions here as a fallback, although buttons are already disabled
        if self.permisos.get(nombre, 0) == 0:
            self._mostrar_alerta_sin_permisos()
            return

        # Use a dictionary or 'match/case' for cleaner action handling
        actions = {
            "Ventas": lambda: subprocess.Popen(["python", "ventas_menu.py"]),
            "Inventario": lambda: subprocess.Popen(["python", "inventario_menu.py"]),
            # Estas funciones requieren la existencia de los módulos importados
            "Clientes": iniciar_clientes,
            "Reportes": iniciar_reportes,
            "Configuración": iniciar_configuracion,
            "Gastos": iniciar_gastos,
            "Usuarios": iniciar_usuarios,
        }
        
        action = actions.get(nombre)
        if action:
            action()

# --- Entry point from login ---
def iniciar_dashboard(usuario, datos_usuario):
    """
    Función de entrada principal para lanzar el dashboard.
    Esta es la función que se llamaría desde la pantalla de login.
    """
    app = VmPOSDashboard(usuario=usuario, datos_usuario=datos_usuario)
    app.mainloop()

# --- Main entry point for standalone testing (ejecutar este archivo directamente) ---
if __name__ == "__main__":
    # Simular una llamada desde la pantalla de login
    # para probar los diferentes roles.
    
    # Usuario Administrador
    mock_admin_data = {'usuario': 'Eduardo', 'permisos': 'admin'}
    print(f"Probando con usuario: {mock_admin_data['usuario']} ({mock_admin_data['permisos']})")
    iniciar_dashboard(mock_admin_data['usuario'], mock_admin_data)

    # # Usuario Vendedor
    # mock_vendedor_data = {'usuario': 'Andres', 'permisos': 'vendedor'}
    # print(f"Probando con usuario: {mock_vendedor_data['usuario']} ({mock_vendedor_data['permisos']})")
    # iniciar_dashboard(mock_vendedor_data['usuario'], mock_vendedor_data)
