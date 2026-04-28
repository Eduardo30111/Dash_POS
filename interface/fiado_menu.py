# -*- coding: utf-8 -*-
"""Cobro de ventas a fiado: perfiles por cédula, deuda acumulada, abonos y edición de datos (no montos)."""
import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

from fiado_db import (
    actualizar_nombre_cliente,
    cambiar_cedula_cliente_fiado,
    ensure_fiado_schema,
    listar_abonos,
    listar_perfiles_fiado,
    listar_ventas_fiado,
    nombre_para_documento,
    registrar_abono,
    saldo_pendiente,
    upsert_cliente_por_cedula,
)
from paths import ventas_db_path
from layout_responsive import bind_reflow_pack, centrar_ventana, crear_cuerpo_modulo_scroll, modulo_scroll_finalizar
from ui_theme import T, F_TITLE, F_BODY, F_BODY_B, F_SMALL, F_STAT, style_ttk_treeview_pos


def _formato_peso(n):
    try:
        return f"${float(n):,.0f}"
    except (TypeError, ValueError):
        return "$0"


def iniciar_fiado(parent=None):
    if parent is not None:
        ventana = tk.Toplevel(parent)
        try:
            ventana.transient(parent)
        except tk.TclError:
            pass
    else:
        ventana = tk.Tk()
    ventana.title("Fiados - VmPOS")
    if parent is not None:
        from navegacion_ventanas import instalar_barra_volver

        instalar_barra_volver(ventana, parent)
    else:
        from layout_responsive import configurar_ventana_modulo

        configurar_ventana_modulo(ventana, min_w=880, min_h=560, ratio_w=0.9, ratio_h=0.86)
    ventana.resizable(True, True)
    ventana.configure(bg=T.BG_APP)

    ruta = ventas_db_path()
    if not os.path.exists(ruta):
        messagebox.showwarning("Base de datos", f"No se encontró ventas.db.\n{ruta}", parent=ventana)
    else:
        with sqlite3.connect(ruta) as conn:
            ensure_fiado_schema(conn)

    doc_var = tk.StringVar()
    saldo_var = tk.StringVar(value="Deuda pendiente: —")

    cuerpo = crear_cuerpo_modulo_scroll(ventana, bg=T.BG_APP)

    top = tk.Frame(cuerpo, bg=T.POS_HEADER, height=76)
    top.pack(fill="x")
    top.pack_propagate(False)
    hl = tk.Frame(top, bg=T.POS_HEADER)
    hl.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=(12, 14))
    tk.Label(hl, text="Cobro de fiados", font=F_TITLE, bg=T.POS_HEADER, fg=T.WHITE).pack(anchor="w")
    tk.Label(
        hl,
        text="Las ventas en «Fiado» desde Ventas se acumulan por cédula. Elija una cuenta, abone o pague; "
        "puede editar nombre o cédula (los montos solo cambian con abono o pago total).",
        font=F_SMALL,
        bg=T.POS_HEADER,
        fg=T.HEADER_TEXT_DIM,
        wraplength=820,
        justify="left",
    ).pack(anchor="w", pady=(4, 0))

    # — Lista de cuentas (perfiles)
    prof_outer = tk.Frame(cuerpo, bg=T.BG_APP)
    prof_outer.pack(fill="x", padx=16, pady=(12, 8))
    prof_card = tk.Frame(prof_outer, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
    prof_card.pack(fill="x")
    tk.Frame(prof_card, bg=T.STAT_2, height=3).pack(fill="x")
    prow = tk.Frame(prof_card, bg=T.BG_CARD)
    prow.pack(fill="x", padx=12, pady=(8, 4))
    tk.Label(prow, text="Cuentas (por cédula / documento)", font=F_BODY_B, bg=T.BG_CARD, fg=T.TEXT).pack(side="left")
    btn_row = tk.Frame(prof_card, bg=T.BG_CARD)
    btn_row.pack(fill="x", padx=8, pady=(0, 6))

    st = ttk.Style()
    style_ttk_treeview_pos(st, T.BG_APP)

    t_perf = ttk.Treeview(
        prof_card,
        columns=("cedula", "nombre", "deuda"),
        show="headings",
        height=5,
        selectmode="browse",
    )
    t_perf.heading("cedula", text="Cédula / documento")
    t_perf.heading("nombre", text="Nombre")
    t_perf.heading("deuda", text="Deuda pendiente")
    t_perf.column("cedula", width=140, anchor="w")
    t_perf.column("nombre", width=220, anchor="w")
    t_perf.column("deuda", width=120, anchor="e")
    spf = ttk.Scrollbar(prof_card, orient="vertical", command=t_perf.yview)
    t_perf.configure(yscrollcommand=spf.set)
    t_perf.pack(side="left", fill="both", expand=True, padx=(12, 0), pady=(0, 10))
    spf.pack(side="right", fill="y", pady=(0, 10), padx=(0, 12))

    search_outer = tk.Frame(cuerpo, bg=T.BG_APP)
    search_outer.pack(fill="x", padx=16, pady=(0, 8))
    search = tk.Frame(search_outer, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
    search.pack(fill="x")
    tk.Frame(search, bg=T.STAT_1, height=3).pack(fill="x")
    search_row = tk.Frame(search, bg=T.BG_CARD)
    search_row.pack(fill="x", padx=12, pady=10)
    tk.Label(search_row, text="Cédula / documento", font=F_BODY_B, bg=T.BG_CARD, fg=T.TEXT).pack(side="left", padx=(0, 8))
    ent = tk.Entry(
        search_row,
        textvariable=doc_var,
        font=F_BODY,
        width=22,
        relief="flat",
        bd=0,
        highlightthickness=1,
        highlightbackground=T.INPUT_BORDER,
    )
    ent.pack(side="left", padx=(0, 12), ipady=4)

    info_saldo = tk.Label(
        search_row,
        textvariable=saldo_var,
        font=F_STAT,
        bg=T.BG_CARD,
        fg=T.TEXT,
    )
    info_saldo.pack(side="right", padx=(8, 0))

    pan_host = tk.Frame(cuerpo, bg=T.BG_APP)
    pan_host.pack(fill=tk.BOTH, expand=True, padx=16, pady=(4, 8))

    def _card_tabla(titulo: str):
        outer = tk.Frame(pan_host, bg=T.BG_APP)
        card = tk.Frame(outer, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True)
        tk.Frame(card, bg=T.POS_HEADER, height=3).pack(fill="x")
        tk.Label(card, text=titulo, font=F_BODY_B, bg=T.BG_CARD, fg=T.TEXT).pack(anchor="w", padx=10, pady=(8, 4))
        body = tk.Frame(card, bg=T.BG_CARD)
        body.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 6))
        return outer, body

    f1, body1 = _card_tabla("Ventas a fiado (cargos)")
    f2, body2 = _card_tabla("Abonos realizados")

    bind_reflow_pack(
        pan_host,
        [
            (
                f1,
                {"side": tk.LEFT, "fill": tk.BOTH, "expand": True, "padx": (0, 6)},
                {"fill": tk.BOTH, "expand": True, "pady": (0, 8)},
            ),
            (
                f2,
                {"side": tk.LEFT, "fill": tk.BOTH, "expand": True, "padx": (6, 0)},
                {"fill": tk.BOTH, "expand": True},
            ),
        ],
        umbral=820,
        debounce_ms=80,
    )

    t_ventas = ttk.Treeview(
        body1, columns=("id", "fecha", "hora", "total"), show="headings", height=7, selectmode="browse"
    )
    for c, t, w in (("id", "ID", 50), ("fecha", "Fecha", 100), ("hora", "Hora", 80), ("total", "Total", 100)):
        t_ventas.heading(c, text=t)
        t_ventas.column(c, width=w, anchor="center")
    sy1 = ttk.Scrollbar(body1, orient="vertical", command=t_ventas.yview)
    t_ventas.configure(yscrollcommand=sy1.set)
    t_ventas.pack(side="left", fill="both", expand=True, padx=2, pady=2)
    sy1.pack(side="right", fill="y")

    t_abonos = ttk.Treeview(
        body2, columns=("fecha", "hora", "monto", "nota"), show="headings", height=7, selectmode="browse"
    )
    for c, t, w in (("fecha", "Fecha", 100), ("hora", "Hora", 80), ("monto", "Monto", 100), ("nota", "Nota", 160)):
        t_abonos.heading(c, text=t)
        t_abonos.column(c, width=w, anchor="center")
    sy2 = ttk.Scrollbar(body2, orient="vertical", command=t_abonos.yview)
    t_abonos.configure(yscrollcommand=sy2.set)
    t_abonos.pack(side="left", fill="both", expand=True, padx=2, pady=2)
    sy2.pack(side="right", fill="y")

    pago_outer = tk.Frame(cuerpo, bg=T.BG_APP)
    pago_outer.pack(fill="x", padx=16, pady=(0, 12))
    pago = tk.Frame(pago_outer, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
    pago.pack(fill="x")
    tk.Frame(pago, bg=T.STAT_3, height=3).pack(fill="x")
    pago_row = tk.Frame(pago, bg=T.BG_CARD)
    pago_row.pack(fill="x", padx=12, pady=10)
    tk.Label(pago_row, text="Monto a abonar", font=F_BODY_B, bg=T.BG_CARD, fg=T.TEXT).pack(side="left", padx=(0, 8))
    monto_var = tk.StringVar()
    monto_e = tk.Entry(
        pago_row,
        textvariable=monto_var,
        font=F_BODY,
        width=14,
        relief="flat",
        bd=0,
        highlightthickness=1,
        highlightbackground=T.INPUT_BORDER,
    )
    monto_e.pack(side="left", padx=(0, 16), ipady=4)
    nota_var = tk.StringVar()
    tk.Label(pago_row, text="Nota (opcional)", font=F_BODY_B, bg=T.BG_CARD, fg=T.TEXT).pack(side="left", padx=(0, 8))
    nota_e = tk.Entry(
        pago_row,
        textvariable=nota_var,
        font=F_BODY,
        width=26,
        relief="flat",
        bd=0,
        highlightthickness=1,
        highlightbackground=T.INPUT_BORDER,
    )
    nota_e.pack(side="left", padx=(0, 8), ipady=4)

    def refrezcar_perfiles():
        t_perf.delete(*t_perf.get_children())
        if not os.path.exists(ruta):
            return
        for ced, nom, deu in listar_perfiles_fiado():
            t_perf.insert("", tk.END, iid=ced, values=(ced, nom or "—", _formato_peso(deu)))

    def aplicar_documento_sel(doc: str):
        doc_var.set((doc or "").strip())
        refrezcar_tablas()

    def refrezcar_tablas():
        t_ventas.delete(*t_ventas.get_children())
        t_abonos.delete(*t_abonos.get_children())
        doc = doc_var.get().strip()
        if not doc or not os.path.exists(ruta):
            saldo_var.set("Deuda pendiente: —")
            refrezcar_perfiles()
            return
        s = saldo_pendiente(doc)
        saldo_var.set(f"Deuda pendiente: {_formato_peso(s)}")
        for r in listar_ventas_fiado(doc):
            iid, fe, ho, tot = r
            t_ventas.insert("", tk.END, values=(iid, fe or "—", ho or "—", _formato_peso(tot or 0)))
        for r in listar_abonos(doc):
            fe, ho, m, n = r
            t_abonos.insert("", tk.END, values=(fe or "—", ho or "—", _formato_peso(m or 0), (n or "")[:80]))
        refrezcar_perfiles()
        # Resaltar fila del documento actual en la lista superior
        try:
            if t_perf.exists(doc):
                t_perf.selection_set(doc)
                t_perf.focus(doc)
                t_perf.see(doc)
        except tk.TclError:
            pass

    def on_perfil_select(_event=None):
        sel = t_perf.selection()
        if not sel:
            return
        ced = sel[0]
        aplicar_documento_sel(ced)

    t_perf.bind("<<TreeviewSelect>>", on_perfil_select)
    t_perf.bind("<Double-1>", lambda e: on_perfil_select())

    def buscar():
        if not doc_var.get().strip():
            messagebox.showwarning("Documento", "Ingrese el número de cédula o documento.", parent=ventana)
            return
        refrezcar_tablas()
        doc = doc_var.get().strip()
        s = saldo_pendiente(doc)
        if s <= 0 and listar_ventas_fiado(doc):
            messagebox.showinfo(
                "Sin deuda pendiente",
                "No hay saldo pendiente a fiado para este documento; puede revisar el historial abajo.",
                parent=ventana,
            )

    def abonar():
        doc = doc_var.get().strip()
        if not doc:
            messagebox.showwarning("Documento", "Seleccione una cuenta o ingrese la cédula.", parent=ventana)
            return
        try:
            m = float((monto_var.get() or "0").replace(",", ".").strip())
        except ValueError:
            messagebox.showerror("Monto", "Ingrese un monto válido.", parent=ventana)
            return
        if m <= 0:
            messagebox.showwarning("Monto", "El monto debe ser mayor que cero.", parent=ventana)
            return
        pend = saldo_pendiente(doc)
        if pend <= 0:
            messagebox.showinfo("Nada que cobrar", "Este documento no tiene deuda pendiente a fiado.", parent=ventana)
            return
        if m > pend:
            if not messagebox.askyesno(
                "Abono mayor a la deuda",
                f"El abono ({_formato_peso(m)}) supera la deuda ({_formato_peso(pend)}).\n¿Registrar igual el abono por {_formato_peso(m)}?",
                parent=ventana,
            ):
                return
        if not registrar_abono(doc, m, nota_var.get()):
            messagebox.showerror("Error", "No se pudo registrar el abono.", parent=ventana)
            return
        monto_var.set("")
        nota_var.set("")
        refrezcar_tablas()
        n_saldo = saldo_pendiente(doc)
        messagebox.showinfo("Abono registrado", f"Nuevo saldo pendiente: {_formato_peso(n_saldo)}", parent=ventana)

    def pagar_todo():
        doc = doc_var.get().strip()
        if not doc:
            messagebox.showwarning("Documento", "Seleccione una cuenta o ingrese la cédula.", parent=ventana)
            return
        pend = saldo_pendiente(doc)
        if pend <= 0:
            messagebox.showinfo("Nada que cobrar", "No hay saldo pendiente.", parent=ventana)
            return
        monto_var.set(str(pend).replace(".", ","))
        if not messagebox.askyesno(
            "Pagar total",
            f"Se registrará un abono de {_formato_peso(pend)} y quedará la cuenta en cero (saldo 0).",
            parent=ventana,
        ):
            return
        if not registrar_abono(doc, pend, "Pago total fiado"):
            messagebox.showerror("Error", "No se pudo registrar el pago.", parent=ventana)
            return
        refrezcar_tablas()
        messagebox.showinfo("Listo", "Cuenta saldada.", parent=ventana)

    def dialogo_nuevo_perfil():
        w = tk.Toplevel(ventana)
        w.title("Nuevo perfil (fiado)")
        w.configure(bg=T.BG_APP)
        w.transient(ventana)
        w.grab_set()
        centrar_ventana(w, 420, 220, ventana)
        f = tk.Frame(w, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
        f.pack(fill="both", expand=True, padx=16, pady=16)
        tk.Label(f, text="Cédula / documento", font=F_BODY_B, bg=T.BG_CARD, fg=T.TEXT).grid(row=0, column=0, sticky="w", padx=12, pady=(12, 4))
        v_ced = tk.StringVar()
        tk.Entry(f, textvariable=v_ced, font=F_BODY, width=32).grid(row=0, column=1, padx=12, pady=(12, 4), sticky="ew")
        tk.Label(f, text="Nombre", font=F_BODY_B, bg=T.BG_CARD, fg=T.TEXT).grid(row=1, column=0, sticky="w", padx=12, pady=4)
        v_nom = tk.StringVar()
        tk.Entry(f, textvariable=v_nom, font=F_BODY, width=32).grid(row=1, column=1, padx=12, pady=4, sticky="ew")
        f.grid_columnconfigure(1, weight=1)

        def guardar_np():
            c = v_ced.get().strip()
            n = v_nom.get().strip()
            if not c:
                messagebox.showwarning("Datos", "La cédula es obligatoria.", parent=w)
                return
            if not n:
                messagebox.showwarning("Datos", "El nombre es obligatorio.", parent=w)
                return
            ok, err = actualizar_nombre_cliente(c, n)
            if not ok:
                messagebox.showerror("Error", err, parent=w)
                return
            w.destroy()
            refrezcar_perfiles()
            doc_var.set(c)
            refrezcar_tablas()
            messagebox.showinfo("Listo", "Perfil creado. Cuando haga una venta fiado con esta cédula, la deuda aparecerá aquí.", parent=ventana)

        tk.Button(f, text="Guardar", command=guardar_np, bg=T.STAT_3, fg=T.WHITE, font=F_BODY_B, relief="flat", padx=14, pady=6).grid(
            row=2, column=1, sticky="e", padx=12, pady=16
        )
        tk.Button(f, text="Cancelar", command=w.destroy, bg=T.POS_BTN_ALT, fg=T.WHITE, font=F_BODY_B, relief="flat", padx=14, pady=6).grid(
            row=2, column=0, sticky="w", padx=12, pady=16
        )

    def dialogo_editar_ficha():
        doc = doc_var.get().strip()
        if not doc:
            messagebox.showwarning("Selección", "Seleccione una cuenta en la lista o busque por cédula.", parent=ventana)
            return
        w = tk.Toplevel(ventana)
        w.title("Editar datos del cliente")
        w.configure(bg=T.BG_APP)
        w.transient(ventana)
        w.grab_set()
        centrar_ventana(w, 440, 280, ventana)
        f = tk.Frame(w, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
        f.pack(fill="both", expand=True, padx=16, pady=16)
        tk.Label(
            f,
            text="Solo nombre y cédula. Los montos de la deuda solo bajan con abonos o pago total.",
            font=F_SMALL,
            bg=T.BG_CARD,
            fg=T.TEXT_MUTED,
            wraplength=400,
            justify="left",
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(8, 12))
        tk.Label(f, text="Nombre", font=F_BODY_B, bg=T.BG_CARD, fg=T.TEXT).grid(row=1, column=0, sticky="w", padx=12, pady=4)
        v_nom = tk.StringVar(value=nombre_para_documento(doc) or "")
        tk.Entry(f, textvariable=v_nom, font=F_BODY, width=34).grid(row=1, column=1, padx=12, pady=4, sticky="ew")
        tk.Label(f, text="Cédula / documento", font=F_BODY_B, bg=T.BG_CARD, fg=T.TEXT).grid(row=2, column=0, sticky="w", padx=12, pady=4)
        v_ced = tk.StringVar(value=doc)
        tk.Entry(f, textvariable=v_ced, font=F_BODY, width=34).grid(row=2, column=1, padx=12, pady=4, sticky="ew")
        f.grid_columnconfigure(1, weight=1)

        def guardar_ed():
            n = v_nom.get().strip()
            nueva = v_ced.get().strip()
            if not n:
                messagebox.showwarning("Datos", "El nombre no puede estar vacío.", parent=w)
                return
            if not nueva:
                messagebox.showwarning("Datos", "La cédula no puede estar vacía.", parent=w)
                return
            if nueva != doc:
                if not messagebox.askyesno(
                    "Cambiar cédula",
                    "Se actualizarán todas las ventas a fiado y abonos vinculados a esta cédula.\n"
                    "No se pueden editar montos de ventas; solo la referencia del documento.\n\n¿Continuar?",
                    parent=w,
                ):
                    return
                ok_c, msg_c = cambiar_cedula_cliente_fiado(doc, nueva)
                if not ok_c:
                    messagebox.showerror("No se pudo cambiar la cédula", msg_c, parent=w)
                    return
                doc_actual = nueva
            else:
                doc_actual = doc
            ok_n, msg_n = actualizar_nombre_cliente(doc_actual, n)
            if not ok_n:
                messagebox.showerror("Error", msg_n, parent=w)
                return
            w.destroy()
            doc_var.set(doc_actual)
            refrezcar_tablas()
            messagebox.showinfo("Listo", "Datos actualizados.", parent=ventana)

        tk.Button(f, text="Guardar", command=guardar_ed, bg=T.STAT_3, fg=T.WHITE, font=F_BODY_B, relief="flat", padx=14, pady=6).grid(
            row=3, column=1, sticky="e", padx=12, pady=16
        )
        tk.Button(f, text="Cancelar", command=w.destroy, bg=T.POS_BTN_ALT, fg=T.WHITE, font=F_BODY_B, relief="flat", padx=14, pady=6).grid(
            row=3, column=0, sticky="w", padx=12, pady=16
        )

    tk.Button(
        btn_row,
        text="Actualizar lista",
        command=lambda: (refrezcar_perfiles(), refrezcar_tablas() if doc_var.get().strip() else None),
        bg=T.POS_BTN_ALT,
        fg=T.WHITE,
        font=F_BODY_B,
        padx=12,
        pady=5,
        relief="flat",
        cursor="hand2",
    ).pack(side="left", padx=4)
    tk.Button(
        btn_row,
        text="Nuevo perfil",
        command=dialogo_nuevo_perfil,
        bg=T.STAT_1,
        fg=T.WHITE,
        font=F_BODY_B,
        padx=12,
        pady=5,
        relief="flat",
        cursor="hand2",
    ).pack(side="left", padx=4)
    tk.Button(
        btn_row,
        text="Editar datos del cliente",
        command=dialogo_editar_ficha,
        bg=T.STAT_2,
        fg=T.WHITE,
        font=F_BODY_B,
        padx=12,
        pady=5,
        relief="flat",
        cursor="hand2",
    ).pack(side="left", padx=4)

    tk.Button(
        search_row,
        text="Buscar",
        command=buscar,
        bg=T.STAT_1,
        fg=T.WHITE,
        font=F_BODY_B,
        padx=16,
        pady=6,
        relief="flat",
        cursor="hand2",
        activebackground="#0284c7",
        activeforeground=T.WHITE,
    ).pack(side="left", padx=4)

    tk.Button(
        pago_row,
        text="Registrar abono",
        command=abonar,
        bg=T.STAT_3,
        fg=T.WHITE,
        font=F_BODY_B,
        padx=14,
        pady=6,
        relief="flat",
        cursor="hand2",
        activebackground=T.POS_BTN_GO_HOVER,
        activeforeground=T.WHITE,
    ).pack(side="left", padx=(12, 6))
    tk.Button(
        pago_row,
        text="Pagar todo",
        command=pagar_todo,
        bg=T.STAT_2,
        fg=T.WHITE,
        font=F_BODY_B,
        padx=12,
        pady=6,
        relief="flat",
        cursor="hand2",
        activebackground="#7c3aed",
        activeforeground=T.WHITE,
    ).pack(side="left", padx=6)

    ent.bind("<Return>", lambda e: buscar())
    monto_e.bind("<Return>", lambda e: abonar())

    refrezcar_perfiles()
    modulo_scroll_finalizar(cuerpo)
    if parent is None:
        ventana.mainloop()


if __name__ == "__main__":
    iniciar_fiado()
