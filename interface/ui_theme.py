# -*- coding: utf-8 -*-
"""
Paleta y tipografía unificada para VmPOS: aspecto de panel profesional (slate + acento rosa).
Úsese en formularios, dashboard y POS; evita rosa neón suelto y mezcla de fuentes Arial/Segoe.
"""
import tkinter as tk


class T:
    """Tokens de color (hex)."""

    BG_APP = "#f1f5f9"
    BG_CARD = "#ffffff"
    BG_SUBTLE = "#f8fafc"
    SIDEBAR = "#0f172a"
    SIDEBAR_HOVER = "#1e293b"
    HEADER_BAR = "#1e293b"
    HEADER_TEXT_DIM = "#94a3b8"
    ACCENT = "#be185d"
    ACCENT_HOVER = "#9d174d"
    ACCENT_LIGHT = "#fce7f3"
    ACCENT_SOFT = "#fbcfe8"
    INPUT_BORDER = "#e2e8f0"
    INPUT_BG = "#ffffff"
    INPUT_BG_ALT = "#f1f5f9"
    TEXT = "#0f172a"
    TEXT_MUTED = "#64748b"
    WHITE = "#ffffff"
    SUCCESS = "#059669"
    SUCCESS_BG = "#d1fae5"
    SUCCESS_BORDER = "#6ee7b7"
    WARN = "#d97706"
    WARN_BG = "#fffbeb"
    DANGER = "#dc2626"
    DANGER_BG = "#fef2f2"
    BORDER = "#e2e8f0"
    DIVIDER = "#cbd5e1"
    FOOTER = "#0f172a"
    LINK = "#2563eb"
    # Barra “Volver al menú” (navegacion_ventanas)
    NAV_BAR = "#312e81"
    NAV_BAR_BTN = "#4f46e5"
    NAV_BAR_BTN_HOVER = "#6366f1"
    # Tarjetas estadísticas (acentos controlados)
    STAT_1 = "#0ea5e9"
    STAT_2 = "#8b5cf6"
    STAT_3 = "#10b981"
    STAT_4 = "#f59e0b"
    # Módulo ventas / POS
    POS_BG = "#f1f5f9"
    POS_HEADER = "#1e293b"
    POS_PANEL = "#ffffff"
    POS_BORDER = "#e2e8f0"
    POS_ACCENT = "#be185d"
    POS_TEXT = "#0f172a"
    POS_MUTED = "#64748b"
    POS_BTN_GO = "#059669"
    POS_BTN_GO_HOVER = "#047857"
    POS_BTN_ALT = "#475569"
    POS_TOTAL_BAR = "#1e293b"
    POS_EMERGENCY_BG = "#fff7ed"
    POS_EMERGENCY_BORDER = "#fed7aa"
    # Pantalla de carga
    SPLASH_OUTER = "#f1f5f9"
    SPLASH_CARD = "#ffffff"
    SPLASH_HEADER = "#1e293b"
    SPLASH_BODY = "#f8fafc"
    SPLASH_ACCENT = "#be185d"


FONT = "Segoe UI"

# Tuplas de fuente reutilizables
F_TITLE = (FONT, 22, "bold")
F_HEAD = (FONT, 16, "bold")
F_SUB = (FONT, 13)
F_BODY = (FONT, 11)
F_BODY_B = (FONT, 11, "bold")
F_SMALL = (FONT, 9)
F_STAT = (FONT, 18, "bold")
F_BTN = (FONT, 11, "bold")


def style_ttk_treeview_pos(style, bg_panel: str = T.POS_BG) -> None:
    """Estilo Treeview y encabezados para el POS (tema clam)."""
    try:
        style.theme_use("clam")
    except (tk.TclError, Exception):
        pass
    style.configure(
        "POS.TLabel",
        background=bg_panel,
        foreground=T.POS_TEXT,
        font=F_BODY,
    )
    style.configure(
        "POSHeader.TLabel",
        background=bg_panel,
        foreground=T.POS_TEXT,
        font=(FONT, 14, "bold"),
    )
    style.configure(
        "Treeview",
        background=T.BG_CARD,
        fieldbackground=T.BG_CARD,
        foreground=T.TEXT,
        rowheight=26,
        font=F_BODY,
    )
    style.configure(
        "Treeview.Heading",
        background=T.POS_HEADER,
        foreground=T.WHITE,
        font=(FONT, 10, "bold"),
    )
    # Hace falta !selected: si solo se mapea "selected", en Windows (ttk/Clam) el texto
    # de filas normales a veces no usa -foreground y queda invisible (tabla "vacía" con total).
    style.map(
        "Treeview",
        background=[("selected", T.ACCENT)],
        foreground=[("selected", T.WHITE), ("!selected", T.TEXT)],
    )


def style_ttk_pos_carrito_treeview(style) -> None:
    """
    Estilo exclusivo para el carrito del POS. En Windows, compartir el nombre de
    estilo 'Treeview' con inventario/búsquedas o un map de foreground incompleto
    deja el texto de las filas invisible aunque el total sí se sume.
    """
    try:
        style.theme_use("clam")
    except (tk.TclError, Exception):
        pass
    s = "POSCarrito.Treeview"
    sh = "POSCarrito.Treeview.Heading"
    style.configure(
        s,
        background=T.BG_CARD,
        fieldbackground=T.BG_CARD,
        foreground="#111827",
        rowheight=28,
        font=F_BODY,
    )
    style.configure(
        sh,
        background=T.POS_HEADER,
        foreground=T.WHITE,
        font=(FONT, 10, "bold"),
    )
    style.map(
        s,
        background=[("selected", T.ACCENT)],
        foreground=[("selected", T.WHITE), ("!selected", "#111827")],
    )
