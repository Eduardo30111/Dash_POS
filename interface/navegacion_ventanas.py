# -*- coding: utf-8 -*-
"""
Navegación entre el dashboard y los módulos: una sola vista útil a la vez
y regreso al menú con un botón explícito.
"""
import tkinter as tk


def instalar_barra_volver(ventana_modulo, dashboard):
    """
    Empaqueta al inicio una barra con «Volver al menú» y enlaza el cierre de la
    ventana para volver a mostrar el dashboard. Llamar antes del resto del layout.

    ``dashboard`` es la ventana principal (VmPOS); si es None, no hace nada.
    """
    if dashboard is None:
        return

    try:
        from layout_responsive import configurar_ventana_modulo

        configurar_ventana_modulo(ventana_modulo)
    except Exception:
        try:
            ventana_modulo.resizable(True, True)
            ventana_modulo.minsize(520, 360)
        except Exception:
            pass

    def volver():
        try:
            ventana_modulo.grab_release()
        except (tk.TclError, Exception):
            pass
        try:
            ventana_modulo.destroy()
        except tk.TclError:
            pass
        try:
            # Traer de nuevo al frente al menú (sin depender de withdraw/deiconify)
            dashboard.wm_deiconify()
            dashboard.lift()
            dashboard.focus_force()
        except tk.TclError:
            pass

    ventana_modulo.protocol("WM_DELETE_WINDOW", volver)
    try:
        from ui_theme import T as _T
    except ImportError:
        class _T:
            NAV_BAR = "#312e81"
            NAV_BAR_BTN = "#4f46e5"
            NAV_BAR_BTN_HOVER = "#6366f1"

    bar = tk.Frame(ventana_modulo, bg=_T.NAV_BAR, height=42)
    bar.pack(side=tk.TOP, fill=tk.X)
    bar.pack_propagate(False)
    tk.Button(
        bar,
        text="←  Volver al menú principal",
        command=volver,
        bg=_T.NAV_BAR_BTN,
        fg="white",
        font=("Segoe UI", 10, "bold"),
        relief=tk.FLAT,
        cursor="hand2",
        activebackground=_T.NAV_BAR_BTN_HOVER,
        activeforeground="white",
        padx=12,
        pady=4,
    ).pack(side=tk.LEFT, padx=10, pady=4)

    # Asegurar que el módulo se vea al frente (en Windows, padre con withdraw
    # impide mostrar Toplevel; aquí forzamos visibilidad.)
    def _traer_modulo_frente():
        try:
            ventana_modulo.wm_deiconify()
            ventana_modulo.update_idletasks()
            ventana_modulo.lift()
            ventana_modulo.focus_force()
        except (tk.TclError, Exception):
            pass

    try:
        ventana_modulo.after(10, _traer_modulo_frente)
    except (tk.TclError, Exception):
        _traer_modulo_frente()


def preparar_ventana_modulo(ventana_modulo, dashboard):
    """
    Coloca la barra «Volver» con pack y devuelve un Frame interior donde debe ir todo el
    contenido del módulo, dentro de un área con scroll vertical (ventanas pequeñas).
    """
    from layout_responsive import crear_cuerpo_modulo_scroll

    if dashboard is not None:
        instalar_barra_volver(ventana_modulo, dashboard)
    try:
        bg = ventana_modulo.cget("bg")
    except tk.TclError:
        bg = "#f5f5f5"
    return crear_cuerpo_modulo_scroll(ventana_modulo, bg=bg)


def abrir_modulo_con_menu_oculto(dashboard, abrir):
    """
    Pone el menú detrás (no lo oculta con withdraw: en Windows eso hace que
    los Toplevel hija no se pinten) y abre el módulo. Si falla, levanta el menú.
    """
    if dashboard is not None:
        try:
            dashboard.update_idletasks()
            dashboard.lower()
        except tk.TclError:
            pass
    try:
        abrir(dashboard)
    except Exception:
        if dashboard is not None:
            try:
                dashboard.wm_deiconify()
                dashboard.lift()
                dashboard.focus_force()
            except tk.TclError:
                pass
        raise
