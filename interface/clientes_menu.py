# -*- coding: utf-8 -*-
import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from paths import ventas_db_path
from layout_responsive import centrar_ventana, crear_cuerpo_modulo_scroll, modulo_scroll_finalizar, bind_reflow_pack
from fiado_db import ensure_fiado_schema
from ui_theme import T, F_TITLE, F_HEAD, F_BODY, F_BODY_B, F_SMALL, F_BTN, F_STAT, style_ttk_treeview_pos


# --- Persistencia: ficha de cliente (tabla `clientes`) ---


def _db_conn():
    p = ventas_db_path()
    if not os.path.exists(p):
        try:
            os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
        except OSError:
            pass
    conn = sqlite3.connect(p)
    ensure_fiado_schema(conn)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clientes'")
    if not c.fetchone():
        c.execute(
            """
            CREATE TABLE clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cedula TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                email TEXT,
                telefono TEXT,
                fecha_registro TEXT NOT NULL
            )
            """
        )
        conn.commit()
    return conn


def db_guardar_ficha(cedula, nombre, email, telefono):
    cedula = (cedula or "").strip()
    nombre = (nombre or "").strip()
    if not cedula or not nombre:
        return False, "Cédula y nombre son obligatorios."
    try:
        conn = _db_conn()
        cur = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("SELECT id FROM clientes WHERE cedula = ?", (cedula,))
        row = cur.fetchone()
        if row:
            cur.execute(
                "UPDATE clientes SET nombre=?, email=?, telefono=?, fecha_registro=? WHERE cedula=?",
                (nombre, email or "", telefono or "", now, cedula),
            )
        else:
            cur.execute(
                "INSERT INTO clientes (cedula, nombre, email, telefono, fecha_registro) VALUES (?,?,?,?,?)",
                (cedula, nombre, email or "", telefono or "", now),
            )
        conn.commit()
        conn.close()
        return True, None
    except sqlite3.Error as e:
        return False, str(e)


def db_obtener_ficha_por_cedula(cedula):
    cedula = (cedula or "").strip()
    if not cedula or cedula.upper() == "N/A":
        return None
    try:
        conn = _db_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, cedula, nombre, IFNULL(email,''), IFNULL(telefono,'') FROM clientes WHERE cedula = ?",
            (cedula,),
        )
        r = cur.fetchone()
        conn.close()
        return r
    except sqlite3.Error:
        return None


def db_actualizar_ficha(id_ficha, cedula, nombre, email, telefono):
    if not cedula or not nombre:
        return False, "Cédula y nombre son obligatorios."
    try:
        conn = _db_conn()
        cur = conn.cursor()
        cur.execute(
            "UPDATE clientes SET cedula=?, nombre=?, email=?, telefono=? WHERE id=?",
            (cedula, nombre, email or "", telefono or "", id_ficha),
        )
        conn.commit()
        conn.close()
        return True, None
    except sqlite3.IntegrityError:
        return False, "Ya existe otra ficha con esa cédula."
    except sqlite3.Error as e:
        return False, str(e)


def db_eliminar_ficha_id(id_ficha):
    try:
        conn = _db_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM clientes WHERE id = ?", (id_ficha,))
        conn.commit()
        n = cur.rowcount
        conn.close()
        return n > 0
    except sqlite3.Error:
        return False


# --- Interfaz ---


def _btn_hover(btn, normal, hover):
    def on_enter(_e):
        btn.config(bg=hover)

    def on_leave(_e):
        btn.config(bg=normal)

    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)


def _form_field(parent, label, show=None):
    tk.Label(parent, text=label, font=F_BODY, bg=T.BG_CARD, fg=T.POS_TEXT, anchor="w").pack(fill=tk.X, pady=(0, 4))
    e = tk.Entry(
        parent,
        font=F_BODY,
        bg=T.INPUT_BG,
        fg=T.POS_TEXT,
        relief=tk.FLAT,
        show=show,
        highlightthickness=1,
        highlightbackground=T.INPUT_BORDER,
    )
    e.pack(fill=tk.X, pady=(0, 12))
    return e


def iniciar_clientes(parent=None):
    if parent is not None:
        ventana = tk.Toplevel(parent)
        try:
            ventana.transient(parent)
        except tk.TclError:
            pass
    else:
        ventana = tk.Tk()
    ventana.title("Clientes - VmPOS")
    if parent is not None:
        from navegacion_ventanas import instalar_barra_volver

        instalar_barra_volver(ventana, parent)
    else:
        from layout_responsive import configurar_ventana_modulo

        configurar_ventana_modulo(ventana, min_w=900, min_h=560, ratio_w=0.9, ratio_h=0.86)
    ventana.resizable(True, True)
    ventana.configure(bg=T.BG_APP)

    footer_frame = tk.Frame(ventana, bg=T.FOOTER, height=40)
    footer_frame.pack_propagate(False)
    footer_frame.pack(side=tk.BOTTOM, fill=tk.X)
    tk.Label(
        footer_frame,
        text="VmPOS · módulo clientes",
        font=F_SMALL,
        bg=T.FOOTER,
        fg=T.HEADER_TEXT_DIM,
    ).pack(expand=True)

    cuerpo = crear_cuerpo_modulo_scroll(ventana, bg=T.BG_APP)

    # — Cabecera
    header_frame = tk.Frame(cuerpo, bg=T.POS_HEADER, height=78)
    header_frame.pack(fill=tk.X)
    header_frame.pack_propagate(False)
    h_left = tk.Frame(header_frame, bg=T.POS_HEADER)
    h_left.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=12)
    tk.Label(
        h_left, text="Clientes", font=F_TITLE, bg=T.POS_HEADER, fg=T.WHITE, anchor="w"
    ).pack(anchor="w")
    tk.Label(
        h_left,
        text="Movimientos por documento y fichas de contacto",
        font=F_SMALL,
        bg=T.POS_HEADER,
        fg=T.HEADER_TEXT_DIM,
        anchor="w",
    ).pack(anchor="w", pady=(2, 0))
    h_right = tk.Frame(header_frame, bg=T.POS_HEADER)
    h_right.pack(side=tk.RIGHT, padx=20, pady=12)
    lbl_fecha = tk.Label(h_right, text="", font=F_SMALL, bg=T.POS_HEADER, fg=T.HEADER_TEXT_DIM, anchor="e")
    lbl_fecha.pack(anchor="e")
    lbl_hora = tk.Label(h_right, text="", font=F_SMALL, bg=T.POS_HEADER, fg=T.WHITE, anchor="e")
    lbl_hora.pack(anchor="e")

    def actualizar_tiempo():
        ahora = datetime.now()
        lbl_fecha.config(text=ahora.strftime("%d %b %Y"))
        lbl_hora.config(text=ahora.strftime("%H:%M:%S"))
        ventana.after(1000, actualizar_tiempo)

    actualizar_tiempo()

    # — Contenido
    main = tk.Frame(cuerpo, bg=T.BG_APP)
    main.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

    # Estadísticas
    total_clientes_var = tk.StringVar(value="0")
    compras_hoy_var = tk.StringVar(value="0")
    ventas_mes_var = tk.StringVar(value="$0")
    var_info_tabla = tk.StringVar(value="")

    def _stat_card(parent, título, var, acento):
        c = tk.Frame(
            parent, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1
        )
        b = tk.Frame(c, bg=acento, height=3)
        b.pack(fill=tk.X)
        tk.Label(c, text=título, font=F_SMALL, bg=T.BG_CARD, fg=T.TEXT_MUTED).pack(anchor="w", padx=12, pady=(10, 2))
        tk.Label(c, textvariable=var, font=F_STAT, bg=T.BG_CARD, fg=acento).pack(anchor="w", padx=12, pady=(0, 10))
        return c

    stats_row = tk.Frame(main, bg=T.BG_APP)
    stats_row.pack(fill="x", pady=(0, 12))
    tarjetas_stats = [
        _stat_card(stats_row, "Clientes (documentos distintos)", total_clientes_var, T.STAT_2),
        _stat_card(stats_row, "Registros hoy", compras_hoy_var, T.STAT_1),
        _stat_card(stats_row, "Suma en el mes (registro)", ventas_mes_var, T.STAT_3),
    ]
    pads_w = ((0, 8), (8, 8), (8, 0))
    bind_reflow_pack(
        stats_row,
        [
            (
                tarjetas_stats[i],
                {"side": tk.LEFT, "fill": tk.BOTH, "expand": True, "padx": pads_w[i]},
                {"fill": tk.X, "pady": (0, 10)},
            )
            for i in range(len(tarjetas_stats))
        ],
        umbral=800,
        debounce_ms=80,
    )

    # Búsqueda
    search_card = tk.Frame(main, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
    search_card.pack(fill=tk.X, pady=(0, 10))
    sf = tk.Frame(search_card, bg=T.BG_CARD)
    sf.pack(fill=tk.X, padx=14, pady=10)
    tk.Label(sf, text="Buscar", font=F_BODY_B, bg=T.BG_CARD, fg=T.POS_TEXT).pack(side=tk.LEFT, padx=(0, 8))
    search_var = tk.StringVar()
    search_entry = tk.Entry(
        sf,
        textvariable=search_var,
        width=32,
        font=F_BODY,
        bg=T.INPUT_BG,
        relief=tk.FLAT,
        highlightthickness=1,
        highlightbackground=T.INPUT_BORDER,
    )
    search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

    def buscar_cliente():
        t = search_var.get().strip()
        if t:
            cargar_datos(filtro_busqueda=t)
        else:
            cargar_datos()

    btn_search = tk.Button(
        sf,
        text="Buscar",
        font=F_BODY_B,
        bg=T.ACCENT,
        fg=T.WHITE,
        padx=16,
        pady=6,
        relief=tk.FLAT,
        cursor="hand2",
        command=buscar_cliente,
        activebackground=T.ACCENT_HOVER,
        activeforeground=T.WHITE,
    )
    btn_search.pack(side=tk.LEFT, padx=4)
    _btn_hover(btn_search, T.ACCENT, T.ACCENT_HOVER)

    btn_ref = tk.Button(
        sf,
        text="Refrescar",
        font=F_BODY_B,
        bg=T.POS_BTN_ALT,
        fg=T.WHITE,
        padx=12,
        pady=6,
        relief=tk.FLAT,
        command=lambda: (search_var.set(""), cargar_datos()),
        activebackground="#334155",
        activeforeground=T.WHITE,
        cursor="hand2",
    )
    btn_ref.pack(side=tk.LEFT, padx=4)
    _btn_hover(btn_ref, T.POS_BTN_ALT, "#334155")

    tk.Label(sf, text="Día", font=F_BODY, bg=T.BG_CARD, fg=T.TEXT_MUTED).pack(side=tk.LEFT, padx=(16, 6))
    filtro_dia_var = tk.StringVar(value="Todos")
    combo_dia = ttk.Combobox(sf, textvariable=filtro_dia_var, state="readonly", width=18, font=F_BODY)
    combo_dia["values"] = ("Todos",)
    combo_dia.pack(side=tk.LEFT, padx=2)
    combo_dia.bind(
        "<<ComboboxSelected>>", lambda e: cargar_datos(filtro_busqueda=search_var.get().strip() or None)
    )

    # Tabla
    table_wrap = tk.Frame(main, bg=T.BG_SUBTLE, highlightbackground=T.BORDER, highlightthickness=1)
    table_wrap.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

    hdr_t = tk.Frame(table_wrap, bg=T.BG_CARD)
    hdr_t.pack(fill=tk.X, padx=1, pady=1)
    tk.Label(hdr_t, text="Movimientos", font=F_HEAD, bg=T.BG_CARD, fg=T.POS_TEXT, anchor="w").pack(
        side=tk.LEFT, padx=10, pady=8
    )
    tk.Label(hdr_t, textvariable=var_info_tabla, font=F_SMALL, bg=T.BG_CARD, fg=T.TEXT_MUTED, anchor="e").pack(
        side=tk.RIGHT, padx=10, pady=8
    )

    table_container = tk.Frame(table_wrap, bg=T.BG_SUBTLE)
    table_container.pack(fill=tk.BOTH, expand=True, padx=1, pady=(0, 1))

    columnas = ("ID", "Documento", "Fecha", "Total Compras", "Estado")
    style = ttk.Style(ventana)
    style_ttk_treeview_pos(style, T.BG_SUBTLE)
    tabla = ttk.Treeview(table_container, columns=columnas, show="headings", height=12)

    for col in columnas:
        tabla.heading(col, text=col)
        w = 120 if col == "ID" else 200
        tabla.column(col, anchor="center", stretch=True, width=w, minwidth=60)

    v_scrollbar = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=tabla.yview)
    h_scrollbar = ttk.Scrollbar(table_container, orient=tk.HORIZONTAL, command=tabla.xview)
    tabla.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
    tabla.grid(row=0, column=0, sticky="nsew")
    v_scrollbar.grid(row=0, column=1, sticky="ns")
    h_scrollbar.grid(row=1, column=0, sticky="ew")
    table_container.rowconfigure(0, weight=1)
    table_container.columnconfigure(0, weight=1)

    # Acciones
    actions = tk.Frame(main, bg=T.BG_APP)
    actions.pack(fill=tk.X, pady=(0, 4))
    a = tk.Frame(actions, bg=T.BG_APP)
    a.pack(fill=tk.X)

    def b_side(txt, cmd, bg, hover, side=tk.LEFT):
        btn = tk.Button(
            a,
            text=txt,
            font=F_BODY_B,
            bg=bg,
            fg=T.WHITE,
            padx=14,
            pady=8,
            relief=tk.FLAT,
            command=cmd,
            cursor="hand2",
            activebackground=hover,
            activeforeground=T.WHITE,
        )
        btn.pack(side=side, padx=4, pady=2)
        _btn_hover(btn, bg, hover)
        return btn

    def conectar_db():
        ruta_db = ventas_db_path()
        if not os.path.exists(ruta_db):
            messagebox.showwarning(
                "Base de Datos",
                f"No se encontró la base. Se usará o creará en:\n{os.path.abspath(ruta_db)}",
            )
        try:
            conn = sqlite3.connect(ruta_db)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ventas'")
            if not cursor.fetchone():
                cursor.execute(
                    """
                    CREATE TABLE ventas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cedula TEXT,
                        nombre TEXT,
                        fecha TEXT,
                        hora TEXT,
                        total REAL,
                        metodo_pago TEXT,
                        productos TEXT
                    )
                    """
                )
                conn.commit()
            ensure_fiado_schema(conn)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clientes'")
            if not cursor.fetchone():
                cursor.execute(
                    """
                    CREATE TABLE clientes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cedula TEXT UNIQUE NOT NULL,
                        nombre TEXT NOT NULL,
                        email TEXT,
                        telefono TEXT,
                        fecha_registro TEXT NOT NULL
                    )
                    """
                )
                conn.commit()
            return conn
        except sqlite3.Error as e:
            messagebox.showerror("Error de Base de Datos", f"Error al conectar:\n{e}\n\nRuta: {ruta_db}")
            return None

    def rellenar_combo_dias():
        conn = conectar_db()
        if not conn:
            return
        try:
            c = conn.cursor()
            c.execute(
                """
                SELECT DISTINCT fecha_compra FROM registro_clientes
                WHERE fecha_compra IS NOT NULL AND TRIM(fecha_compra) != ''
                ORDER BY fecha_compra DESC
                LIMIT 200
                """
            )
            dias = [r[0] for r in c.fetchall() if r[0]]
            sel = filtro_dia_var.get()
            combo_dia["values"] = ("Todos",) + tuple(dias)
            if sel in ("Todos",) + tuple(dias):
                filtro_dia_var.set(sel)
            else:
                filtro_dia_var.set("Todos")
        except sqlite3.Error:
            pass
        finally:
            conn.close()

    def cargar_datos(filtro_busqueda=None):
        tabla.delete(*tabla.get_children())
        conn = conectar_db()
        if not conn:
            messagebox.showerror("Error", "No se pudo conectar a la base de datos")
            return
        dia = filtro_dia_var.get() or "Todos"
        n_rows = 0
        try:
            cursor = conn.cursor()
            conditions = ["1=1"]
            params = []
            if filtro_busqueda:
                t = f"%{filtro_busqueda.strip()}%"
                conditions.append(
                    "(documento LIKE ? OR IFNULL(fecha_compra,'') LIKE ? OR IFNULL(hora_compra,'') LIKE ?)"
                )
                params.extend([t, t, t])
            if dia and dia != "Todos":
                conditions.append("fecha_compra = ?")
                params.append(dia)
            where_sql = " AND ".join(conditions)
            cursor.execute(
                f"""
                SELECT id, documento, fecha_compra, hora_compra, total_compras,
                       LOWER(COALESCE(tipo_pago, 'contado')) AS tp
                FROM registro_clientes
                WHERE {where_sql}
                ORDER BY fecha_compra DESC, hora_compra DESC
                """,
                params,
            )
            resultados = cursor.fetchall()
            for idx, row in enumerate(resultados):
                _id, documento, fecha_compra, hora_compra, total_compras, tp = row
                documento_mostrar = documento if documento else "N/A"
                fecha_mostrar = (
                    f"{fecha_compra} {hora_compra}"
                    if fecha_compra and hora_compra
                    else (fecha_compra or "N/A")
                )
                total_mostrar = f"${total_compras:,.0f}" if total_compras is not None else "$0"
                estado = "Fiado" if (tp or "") == "fiado" else "Contado"
                tag = "even" if idx % 2 == 0 else "odd"
                tabla.insert(
                    "",
                    "end",
                    values=(_id, documento_mostrar, fecha_mostrar, total_mostrar, estado),
                    tags=(tag,),
                )
                n_rows += 1
            tabla.tag_configure("even", background=T.BG_CARD)
            tabla.tag_configure("odd", background=T.BG_SUBTLE)

            cursor.execute(
                "SELECT COUNT(DISTINCT documento) FROM registro_clientes "
                "WHERE documento IS NOT NULL AND TRIM(documento) != ''"
            )
            total_clientes_var.set(str(cursor.fetchone()[0] or 0))
            hoy = datetime.now().strftime("%Y-%m-%d")
            cursor.execute("SELECT COUNT(*) FROM registro_clientes WHERE fecha_compra = ?", (hoy,))
            compras_hoy_var.set(str(cursor.fetchone()[0] or 0))
            cursor.execute(
                "SELECT COALESCE(SUM(total_compras), 0) FROM registro_clientes "
                "WHERE strftime('%Y-%m', IFNULL(fecha_compra, '')) = strftime('%Y-%m', 'now')"
            )
            ventas_mes_var.set(f"${float(cursor.fetchone()[0] or 0):,.0f}")
            var_info_tabla.set(f"{n_rows} filas en la lista")
        except sqlite3.Error as e:
            if "no such table" in str(e).lower() or "no such column" in str(e).lower():
                messagebox.showerror("Error de base de datos", f"{e}\n\nEjecuta una venta o actualiza el módulo.")
            else:
                messagebox.showerror("Error", f"Error al cargar: {e}")
        finally:
            conn.close()
        rellenar_combo_dias()

    def nuevo_cliente():
        w = tk.Toplevel(ventana)
        w.title("Nueva ficha de cliente")
        w.configure(bg=T.BG_APP)
        w.transient(ventana)
        w.grab_set()
        centrar_ventana(w, 420, 400, ventana)
        cap = tk.Frame(w, bg=T.BG_APP)
        cap.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)
        card = tk.Frame(cap, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True)
        tk.Label(card, text="Nueva ficha", font=F_HEAD, bg=T.BG_CARD, fg=T.POS_TEXT, anchor="w").pack(
            anchor="w", padx=16, pady=(16, 4)
        )
        tk.Label(
            card,
            text="La cédula o documento debe coincidir con el que usas en las ventas.",
            font=F_SMALL,
            bg=T.BG_CARD,
            fg=T.TEXT_MUTED,
            wraplength=360,
            justify=tk.LEFT,
        ).pack(anchor="w", padx=16, pady=(0, 8))
        frm = tk.Frame(card, bg=T.BG_CARD)
        frm.pack(fill=tk.BOTH, expand=True, padx=16, pady=4)
        e_ced = _form_field(frm, "Cédula / documento *")
        e_nom = _form_field(frm, "Nombre *")
        e_em = _form_field(frm, "Correo (opcional)")
        e_tel = _form_field(frm, "Teléfono (opcional)")

        def save():
            ok, err = db_guardar_ficha(e_ced.get().strip(), e_nom.get().strip(), e_em.get().strip(), e_tel.get().strip())
            if ok:
                messagebox.showinfo("Listo", "Ficha guardada.", parent=w)
                w.destroy()
                cargar_datos()
            else:
                messagebox.showerror("Error", err or "No se pudo guardar", parent=w)

        btns = tk.Frame(card, bg=T.BG_CARD)
        btns.pack(fill=tk.X, padx=16, pady=16)
        bf = tk.Frame(btns, bg=T.BG_CARD)
        bf.pack(fill=tk.X)
        b_ok = tk.Button(
            bf,
            text="Guardar",
            font=F_BTN,
            bg=T.POS_BTN_GO,
            fg=T.WHITE,
            pady=10,
            relief=tk.FLAT,
            command=save,
            cursor="hand2",
            activebackground=T.POS_BTN_GO_HOVER,
            activeforeground=T.WHITE,
        )
        b_ok.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        _btn_hover(b_ok, T.POS_BTN_GO, T.POS_BTN_GO_HOVER)
        b_x = tk.Button(
            bf,
            text="Cancelar",
            font=F_BODY_B,
            bg=T.POS_BTN_ALT,
            fg=T.WHITE,
            pady=10,
            relief=tk.FLAT,
            command=w.destroy,
            cursor="hand2",
            activebackground="#334155",
            activeforeground=T.WHITE,
        )
        b_x.pack(side=tk.LEFT, fill=tk.X, expand=True)
        _btn_hover(b_x, T.POS_BTN_ALT, "#334155")
        e_ced.focus()

    def editar_ficha():
        sel = tabla.selection()
        if not sel:
            messagebox.showwarning("Selección", "Elige un registro de la lista (usa el documento para la ficha).", parent=ventana)
            return
        v = tabla.item(sel[0])["values"]
        doc = (v[1] or "").strip()
        if not doc or doc.upper() == "N/A":
            messagebox.showinfo("Ficha", "Este registro no tiene documento; no se puede vincular a una ficha.", parent=ventana)
            return
        ficha = db_obtener_ficha_por_cedula(doc)
        if not ficha:
            messagebox.showinfo(
                "Sin ficha",
                f"No hay ficha guardada para «{doc}». Usa «Nueva ficha» con esa misma cédula o documento.",
                parent=ventana,
            )
            return
        _id, ced, nom, em, tel = ficha
        w = tk.Toplevel(ventana)
        w.title("Editar ficha")
        w.configure(bg=T.BG_APP)
        w.transient(ventana)
        w.grab_set()
        centrar_ventana(w, 420, 400, ventana)
        cap = tk.Frame(w, bg=T.BG_APP)
        cap.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)
        card = tk.Frame(cap, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True)
        tk.Label(card, text="Editar ficha de cliente", font=F_HEAD, bg=T.BG_CARD, fg=T.POS_TEXT, anchor="w").pack(
            anchor="w", padx=16, pady=(16, 8)
        )
        frm = tk.Frame(card, bg=T.BG_CARD)
        frm.pack(fill=tk.BOTH, expand=True, padx=16, pady=4)
        e_ced = _form_field(frm, "Cédula / documento *")
        e_ced.insert(0, ced)
        e_nom = _form_field(frm, "Nombre *")
        e_nom.insert(0, nom)
        e_em = _form_field(frm, "Correo (opcional)")
        e_em.insert(0, em)
        e_tel = _form_field(frm, "Teléfono (opcional)")
        e_tel.insert(0, tel)

        def save():
            ok, err = db_actualizar_ficha(
                _id, e_ced.get().strip(), e_nom.get().strip(), e_em.get().strip(), e_tel.get().strip()
            )
            if ok:
                messagebox.showinfo("Listo", "Ficha actualizada.", parent=w)
                w.destroy()
                cargar_datos()
            else:
                messagebox.showerror("Error", err or "No se pudo actualizar", parent=w)

        btns = tk.Frame(card, bg=T.BG_CARD)
        btns.pack(fill=tk.X, padx=16, pady=16)
        bf = tk.Frame(btns, bg=T.BG_CARD)
        bf.pack(fill=tk.X)
        b_ok = tk.Button(
            bf,
            text="Guardar cambios",
            font=F_BTN,
            bg=T.ACCENT,
            fg=T.WHITE,
            pady=10,
            relief=tk.FLAT,
            command=save,
            cursor="hand2",
            activebackground=T.ACCENT_HOVER,
            activeforeground=T.WHITE,
        )
        b_ok.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        _btn_hover(b_ok, T.ACCENT, T.ACCENT_HOVER)
        b_x = tk.Button(
            bf,
            text="Cancelar",
            font=F_BODY_B,
            bg=T.POS_BTN_ALT,
            fg=T.WHITE,
            pady=10,
            relief=tk.FLAT,
            command=w.destroy,
            cursor="hand2",
            activebackground="#334155",
            activeforeground=T.WHITE,
        )
        b_x.pack(side=tk.LEFT, fill=tk.X, expand=True)
        _btn_hover(b_x, T.POS_BTN_ALT, "#334155")
        e_nom.focus()

    def eliminar_ficha():
        sel = tabla.selection()
        if not sel:
            messagebox.showwarning("Selección", "Elige un registro con documento.", parent=ventana)
            return
        doc = (tabla.item(sel[0])["values"][1] or "").strip()
        if not doc or doc.upper() == "N/A":
            return
        ficha = db_obtener_ficha_por_cedula(doc)
        if not ficha:
            messagebox.showinfo("Sin ficha", f"No hay ficha en clientes para «{doc}».", parent=ventana)
            return
        if not messagebox.askyesno(
            "Confirmar", f"¿Eliminar la ficha de clientes de «{doc}»? (no borra el historial de ventas).", parent=ventana
        ):
            return
        if db_eliminar_ficha_id(ficha[0]):
            messagebox.showinfo("Listo", "Ficha eliminada.", parent=ventana)
            cargar_datos()
        else:
            messagebox.showerror("Error", "No se pudo eliminar.", parent=ventana)

    def ver_historial_cliente():
        seleccion = tabla.selection()
        if not seleccion:
            messagebox.showwarning("Selección", "Selecciona un registro con documento.", parent=ventana)
            return
        cedula = (tabla.item(seleccion[0])["values"][1] or "").strip()
        if not cedula or cedula.upper() == "N/A":
            messagebox.showinfo("Historial", "No hay documento en esta fila.", parent=ventana)
            return
        ventana_historial = tk.Toplevel(ventana)
        ventana_historial.title(f"Historial — {cedula}")
        ventana_historial.configure(bg=T.BG_APP)
        centrar_ventana(ventana_historial, 820, 520, ventana)
        ventana_historial.transient(ventana)
        cap = tk.Frame(ventana_historial, bg=T.BG_APP)
        cap.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)
        tk.Label(
            cap,
            text=f"Ventas con documento {cedula}",
            font=F_HEAD,
            bg=T.BG_APP,
            fg=T.POS_TEXT,
            anchor="w",
        ).pack(anchor="w", pady=(0, 8))
        tw = tk.Frame(cap, bg=T.BG_SUBTLE, highlightbackground=T.BORDER, highlightthickness=1)
        tw.pack(fill=tk.BOTH, expand=True)
        conn = conectar_db()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT fecha_venta, hora_venta, total_venta, COALESCE(tipo_pago, 'contado')
                FROM ventas
                WHERE documento_cliente = ?
                ORDER BY fecha_venta DESC, hora_venta DESC
                """,
                (cedula,),
            )
            historial = cursor.fetchall()
        finally:
            conn.close()

        cols_historial = ("Fecha", "Hora", "Total", "Estado")
        st2 = ttk.Style(ventana_historial)
        style_ttk_treeview_pos(st2, T.BG_SUBTLE)
        tabla_historial = ttk.Treeview(tw, columns=cols_historial, show="headings", height=14)
        for c in cols_historial:
            tabla_historial.heading(c, text=c)
            tabla_historial.column(c, width=160, anchor="center", stretch=True)
        sy = ttk.Scrollbar(tw, orient=tk.VERTICAL, command=tabla_historial.yview)
        tabla_historial.configure(yscrollcommand=sy.set)
        tabla_historial.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=1, pady=1)
        sy.pack(side=tk.RIGHT, fill=tk.Y, pady=1)

        total_gastado = 0.0
        for registro in historial:
            fecha, hora, total, tp = registro
            estado = "Fiado" if (tp or "").lower() == "fiado" else "Contado"
            tabla_historial.insert(
                "", "end", values=(fecha or "N/A", hora or "N/A", f"${(total or 0):,.0f}", estado)
            )
            if total:
                total_gastado += float(total)
        sf = tk.Frame(cap, bg=T.BG_APP)
        sf.pack(fill=tk.X, pady=10)
        tk.Label(
            sf,
            text=f"Total (suma de la tabla): {total_gastado:,.0f} COP",
            font=F_BODY_B,
            bg=T.BG_APP,
            fg=T.POS_TEXT,
        ).pack(anchor="w")
        tk.Button(
            cap,
            text="Cerrar",
            font=F_BODY_B,
            bg=T.POS_BTN_ALT,
            fg=T.WHITE,
            padx=20,
            pady=8,
            relief=tk.FLAT,
            command=ventana_historial.destroy,
            cursor="hand2",
        ).pack(anchor=tk.E)

    b_side("Nueva ficha", nuevo_cliente, T.ACCENT, T.ACCENT_HOVER)
    b_side("Editar ficha", editar_ficha, T.STAT_1, "#0284c7")
    b_side("Historial", ver_historial_cliente, T.STAT_2, "#7c3aed")
    b_side("Eliminar ficha", eliminar_ficha, T.DANGER, "#b91c1c")

    search_entry.bind("<Return>", lambda e: buscar_cliente())

    modulo_scroll_finalizar(cuerpo)

    def keyboard_shortcuts(event):
        if event.state & 0x4:
            k = event.keysym.lower()
            if k == "f":
                search_entry.focus()
            elif k == "r":
                cargar_datos()

    ventana.bind("<KeyPress>", keyboard_shortcuts)
    ventana.focus_set()

    cargar_datos()

    if parent is None:
        ventana.mainloop()


if __name__ == "__main__":
    iniciar_clientes()
