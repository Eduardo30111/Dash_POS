# -*- coding: utf-8 -*-
"""
Utilidades de ventana: tamaño según la pantalla, mínimo usable y expansión (grid).
Úsese en todos los módulos (Toplevel / Tk) para que el contenido se adapte al redimensionar.
"""
import sys
import tkinter as tk
from tkinter import ttk


def centrar_ventana(ventana, ancho, alto, padre=None):
    """
    Centra una ``Tk`` o ``Toplevel`` en la pantalla o, si se indica ``padre``,
    en el área del widget padre (típico para modales sobre el menú).
    """
    try:
        ventana.update_idletasks()
    except (tk.TclError, Exception):
        pass
    x, y = 0, 0
    usado_padre = False
    if padre is not None:
        try:
            padre.update_idletasks()
            px = int(padre.winfo_rootx())
            py = int(padre.winfo_rooty())
            pw = int(padre.winfo_width())
            ph = int(padre.winfo_height())
            x = px + (pw - ancho) // 2
            y = py + (ph - alto) // 2
            usado_padre = True
        except (tk.TclError, Exception):
            pass
    if not usado_padre:
        try:
            sw = int(ventana.winfo_screenwidth() or 1024)
            sh = int(ventana.winfo_screenheight() or 768)
            x = max(0, (sw - ancho) // 2)
            y = max(0, (sh - alto) // 2)
        except (tk.TclError, Exception):
            x, y = 0, 0
    try:
        ventana.geometry(f"{ancho}x{alto}+{int(x)}+{int(y)}")
    except (tk.TclError, Exception):
        pass


def configurar_ventana_modulo(
    ventana,
    min_w: int = 520,
    min_h: int = 360,
    ratio_w: float = 0.90,
    ratio_h: float = 0.86,
) -> None:
    """
    Ventana redimensionable, tamaño inicial acorde a la resolución, sin pasarse del monitor.
    """
    try:
        ventana.resizable(True, True)
        ventana.minsize(min_w, min_h)
    except (tk.TclError, Exception):
        return
    ventana.update_idletasks()
    try:
        sw = int(ventana.winfo_screenwidth() or 1024)
        sh = int(ventana.winfo_screenheight() or 768)
    except (tk.TclError, Exception):
        sw, sh = 1024, 768
    w = max(min_w, int(sw * ratio_w))
    h = max(min_h, int(sh * ratio_h))
    w = min(w, sw - 8)
    h = min(h, sh - 8)
    x = (sw - w) // 2
    y = (sh - h) // 2
    try:
        ventana.geometry(f"{w}x{h}+{x}+{y}")
    except (tk.TclError, Exception):
        pass
    if sys.platform == "win32":
        try:
            ventana.state("normal")
        except (tk.TclError, Exception):
            pass


def refrescar_region_scroll(canvas: tk.Canvas) -> None:
    """Actualiza scrollregion tras cambiar hijos del frame interno del canvas."""
    try:
        canvas.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all") or (0, 0, 0, 0))
    except (tk.TclError, Exception):
        pass


def crear_cuerpo_modulo_scroll(parent: tk.Misc, bg: str = "#f5f5f5") -> tk.Frame:
    """
    Empaqueta en ``parent`` un Canvas con barra vertical y devuelve el Frame interior
    donde debe ir todo el contenido del módulo. Así, en ventanas bajas o estrechas
    el usuario puede hacer scroll sin perder TOTAL / botones / pie.

    No enlaza la rueda a ``ttk.Treeview`` (siguen usando su scroll interno).
    """
    sb = ttk.Scrollbar(parent, orient=tk.VERTICAL)
    cv = tk.Canvas(parent, bg=bg, highlightthickness=0)
    inner = tk.Frame(cv, bg=bg)
    win_id = cv.create_window((0, 0), window=inner, anchor=tk.NW)
    sb["command"] = cv.yview
    cv["yscrollcommand"] = sb.set
    sb.pack(side=tk.RIGHT, fill=tk.Y)
    cv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _sync_embedded(_e=None):
        """
        Ancho del frame = viewport; alto = máximo(contenido, viewport).
        Sin esto el inner sólo crece hasta su tamaño solicitado y no rellena
        ventanas altas (tablas con expand=True parecen cortadas sin ocupar hueco).
        """
        try:
            cv.update_idletasks()
            cw = max(1, int(cv.winfo_width()))
            ch = max(1, int(cv.winfo_height()))
            inner.update_idletasks()
            reqh = int(inner.winfo_reqheight())
            nh = max(reqh, ch)
            cv.itemconfig(win_id, width=cw, height=nh)
            refrescar_region_scroll(cv)
        except (tk.TclError, Exception):
            pass

    inner.bind("<Configure>", lambda _e: _sync_embedded())
    cv.bind("<Configure>", lambda e: _sync_embedded(e))

    def _on_wheel(event):
        d = 0
        if getattr(event, "delta", 0):
            d = int(-1 * (event.delta // 120)) or (-1 if event.delta > 0 else 1)
        elif event.num == 4:
            d = -1
        elif event.num == 5:
            d = 1
        if d:
            cv.yview_scroll(d * 3, "units")

    def _bind_wheel_recurse(w):
        if isinstance(w, ttk.Treeview):
            return
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            w.bind(seq, _on_wheel)
        for ch in w.winfo_children():
            _bind_wheel_recurse(ch)

    for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
        cv.bind(seq, _on_wheel)
        sb.bind(seq, _on_wheel)

    # Tras el primer idle, por si el padre aún no tiene tamaño
    try:
        parent.after_idle(_sync_embedded)
    except (tk.TclError, Exception):
        pass

    # Guardar para repost bind si el módulo añade widgets después + sync tras construir UI
    inner._vmpos_scroll_canvas = cv  # type: ignore[attr-defined]
    inner._vmpos_rebind_wheel = lambda: _bind_wheel_recurse(inner)  # type: ignore[attr-defined]
    inner._vmpos_sync_embedded = _sync_embedded  # type: ignore[attr-defined]

    return inner


def modulo_scroll_finalizar(inner: tk.Frame) -> None:
    """Tras crear toda la UI dentro del Frame devuelto por ``crear_cuerpo_modulo_scroll``, llama una vez para enlazar la rueda a los widgets y sincronizar tamaño/región de scroll."""
    rebind = getattr(inner, "_vmpos_rebind_wheel", None)
    if callable(rebind):
        rebind()
    sync = getattr(inner, "_vmpos_sync_embedded", None)
    cv = getattr(inner, "_vmpos_scroll_canvas", None)
    if callable(sync):
        try:
            sync()
        except (tk.TclError, Exception):
            pass
    elif isinstance(cv, tk.Canvas):
        refrescar_region_scroll(cv)


def bind_reflow_pack(
    contenedor: tk.Misc,
    bloques: list[tuple[tk.Widget, dict, dict]],
    umbral: int = 780,
    debounce_ms: int = 80,
) -> None:
    """
    Repack dinámico: con ancho >= ``umbral`` usa ``pack`` con los kwargs del segundo dict;
    si no, con el tercero (típico: fila horizontal vs columna apilada).

    ``bloques``: (widget, kwargs_modo_ancho, kwargs_modo_estrecho)
    Llamar tras haber hecho el ``pack`` inicial de cada widget (o ``pack_forget`` antes de aplicar).
    """
    state: dict = {"estrecho": None, "after_id": None}

    def aplicar():
        try:
            w = int(contenedor.winfo_width())
        except (tk.TclError, Exception):
            return
        if w <= 1:
            return
        estrecho = w < umbral
        if state["estrecho"] is not None and estrecho == state["estrecho"]:
            return
        state["estrecho"] = estrecho
        for wid, _a, _b in bloques:
            try:
                wid.pack_forget()
            except tk.TclError:
                return
        for wid, kw_w, kw_n in bloques:
            kw = kw_n if estrecho else kw_w
            wid.pack(**kw)

    def on_cfg(e):
        if e.widget is not contenedor:
            return
        aid = state.get("after_id")
        if aid is not None:
            try:
                contenedor.after_cancel(aid)
            except (tk.TclError, Exception):
                pass
        state["after_id"] = contenedor.after(debounce_ms, aplicar)

    contenedor.bind("<Configure>", on_cfg, add="+")
    try:
        contenedor.after_idle(aplicar)
    except (tk.TclError, Exception):
        pass


def bind_reflow_pair_header_body(
    contenedor: tk.Misc,
    cabecera: tk.Widget,
    cuerpo: tk.Widget,
    umbral: int = 720,
    debounce_ms: int = 80,
) -> None:
    """
    Modo ancho: cabecera a la izquierda, cuerpo a la derecha (típ. accesos rápidos).
    Modo estrecho: cabecera arriba ``fill=X``, cuerpo debajo ``fill=X``.
    """
    bind_reflow_pack(
        contenedor,
        [
            (cabecera, {"side": tk.LEFT, "padx": (20, 16), "pady": 12}, {"fill": tk.X, "padx": (20, 16), "pady": (12, 4)}),
            (cuerpo, {"side": tk.RIGHT, "padx": (16, 16), "pady": 12}, {"fill": tk.X, "padx": (16, 16), "pady": (0, 12)}),
        ],
        umbral=umbral,
        debounce_ms=debounce_ms,
    )


def bind_reflow_grid_uniform(
    contenedor: tk.Misc,
    hijos: list,
    columnas_cuando_anchas: int = 3,
    umbral: int = 760,
    debounce_ms: int = 80,
    pad_exterior: int = 25,
) -> None:
    """
    Ordena hijos en una rejilla de ``columnas_cuando_anchas`` columnas cuando el ancho es >= ``umbral``;
    si no, una columna apilada (stretch horizontal).
    ``hijos`` debe permanecer estable (misma lista de widgets).
    """
    state: dict = {"estrecho": None, "after_id": None}
    c = max(1, columnas_cuando_anchas)

    def aplicar():
        try:
            aw = int(contenedor.winfo_width())
        except (tk.TclError, Exception):
            return
        if aw <= 1:
            return
        estrecho = aw < umbral
        if state["estrecho"] is not None and estrecho == state["estrecho"]:
            return
        state["estrecho"] = estrecho

        for h in hijos:
            try:
                h.grid_forget()
            except tk.TclError:
                continue

        try:
            for cc in range(12):
                contenedor.grid_columnconfigure(cc, weight=0)
            if estrecho:
                contenedor.grid_columnconfigure(0, weight=1)
            else:
                for cc in range(c):
                    contenedor.grid_columnconfigure(cc, weight=1)
        except tk.TclError:
            pass

        max_r = 0
        for idx, h in enumerate(hijos):
            if estrecho:
                r = idx
                h.grid(row=r, column=0, sticky="ew", padx=pad_exterior, pady=(8 if idx else 10, 10))
            else:
                r = idx // c
                cc = idx % c
                h.grid(row=r, column=cc, sticky="nsew", padx=max(4, pad_exterior // 3), pady=10)
            max_r = max(max_r, r)

        try:
            for ri in range(max_r + 3):
                contenedor.grid_rowconfigure(ri, weight=0)
        except tk.TclError:
            pass

    def on_cfg(e):
        if e.widget is not contenedor:
            return
        aid = state.get("after_id")
        if aid is not None:
            try:
                contenedor.after_cancel(aid)
            except (tk.TclError, Exception):
                pass
        state["after_id"] = contenedor.after(debounce_ms, aplicar)

    contenedor.bind("<Configure>", on_cfg, add="+")
    try:
        contenedor.after_idle(aplicar)
    except (tk.TclError, Exception):
        pass
