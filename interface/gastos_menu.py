import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import sqlite3
import os

from paths import ventas_db_path
from layout_responsive import centrar_ventana, crear_cuerpo_modulo_scroll, modulo_scroll_finalizar
from ui_theme import T, F_TITLE, F_HEAD, F_BODY, F_BODY_B, F_SMALL, F_STAT, style_ttk_treeview_pos

ruta_db = ventas_db_path()

_SQL_GASTOS = """
    CREATE TABLE IF NOT EXISTS gastos (
        id_gasto INTEGER PRIMARY KEY AUTOINCREMENT,
        concepto TEXT NOT NULL,
        valor REAL NOT NULL,
        fecha TEXT NOT NULL,
        hora TEXT NOT NULL,
        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
"""


def asegurar_tabla_gastos():
    """Crea la tabla de gastos si no existe (una conexión corta, sin estado global)."""
    try:
        with sqlite3.connect(ruta_db) as conn:
            conn.execute(_SQL_GASTOS)
            conn.commit()
        return True
    except Exception as e:
        messagebox.showerror("Error de conexión", f"No se pudo preparar la base de datos de gastos:\n{e}")
        return False


def conectar_db():
    """Mantiene nombre por compatibilidad: solo asegura la tabla."""
    return asegurar_tabla_gastos()


def obtener_gastos():
    try:
        with sqlite3.connect(ruta_db) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM gastos ORDER BY fecha_registro DESC")
            return c.fetchall()
    except Exception as e:
        messagebox.showerror("Error", f"Error al obtener gastos: {e}")
        return []


def agregar_gasto_db(concepto, valor, fecha, hora):
    try:
        with sqlite3.connect(ruta_db) as conn:
            conn.execute(
                "INSERT INTO gastos (concepto, valor, fecha, hora) VALUES (?, ?, ?, ?)",
                (concepto, valor, fecha, hora),
            )
            conn.commit()
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Error al agregar gasto: {e}")
        return False


def eliminar_gasto_db(id_gasto):
    try:
        with sqlite3.connect(ruta_db) as conn:
            conn.execute("DELETE FROM gastos WHERE id_gasto = ?", (id_gasto,))
            conn.commit()
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Error al eliminar gasto: {e}")
        return False


def modificar_gasto_db(id_gasto, concepto, valor):
    try:
        with sqlite3.connect(ruta_db) as conn:
            conn.execute(
                "UPDATE gastos SET concepto = ?, valor = ? WHERE id_gasto = ?",
                (concepto, valor, id_gasto),
            )
            conn.commit()
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Error al modificar gasto: {e}")
        return False


def calcular_estadisticas_gastos():
    try:
        with sqlite3.connect(ruta_db) as conn:
            c = conn.cursor()
            c.execute("SELECT COALESCE(SUM(valor), 0) FROM gastos")
            total_gastos = c.fetchone()[0] or 0
            fecha_hoy = datetime.now().strftime("%d-%m-%Y")
            c.execute("SELECT COUNT(*), COALESCE(SUM(valor), 0) FROM gastos WHERE fecha = ?", (fecha_hoy,))
            resultado = c.fetchone()
            gastos_hoy_count = resultado[0] or 0
            gastos_hoy_valor = resultado[1] or 0
            c.execute("SELECT COUNT(*) FROM gastos")
            total_registros = c.fetchone()[0] or 0
        return total_gastos, gastos_hoy_count, gastos_hoy_valor, total_registros
    except Exception as e:
        messagebox.showerror("Error", f"Error al calcular estadísticas: {e}")
        return 0, 0, 0, 0


def iniciar_gastos(parent=None):
    if not asegurar_tabla_gastos():
        if parent is not None:
            try:
                parent.wm_deiconify()
                parent.lift()
                parent.focus_force()
            except tk.TclError:
                pass
        return
    if parent is not None:
        ventana = tk.Toplevel(parent)
        try:
            ventana.transient(parent)
        except tk.TclError:
            pass
    else:
        ventana = tk.Tk()
    ventana.title("Control de Gastos - VmPOS")
    if parent is not None:
        from navegacion_ventanas import instalar_barra_volver
        instalar_barra_volver(ventana, parent)
    else:
        from layout_responsive import configurar_ventana_modulo
        configurar_ventana_modulo(ventana, min_w=1000, min_h=560, ratio_w=0.9, ratio_h=0.86)
    ventana.resizable(True, True)
    ventana.configure(bg=T.BG_APP)

    footer_frame = tk.Frame(ventana, bg=T.FOOTER, height=48)
    footer_frame.pack_propagate(False)
    footer_frame.pack(side=tk.BOTTOM, fill=tk.X)

    cuerpo = crear_cuerpo_modulo_scroll(ventana, bg=T.BG_APP)

    # Variables globales para los campos
    global concepto_var, valor_var, fecha_var, tabla
    concepto_var = tk.StringVar()
    valor_var = tk.StringVar()
    fecha_var = tk.StringVar(value=datetime.now().strftime("%d-%m-%Y"))

    header_frame = tk.Frame(cuerpo, bg=T.POS_HEADER, height=76)
    header_frame.pack(fill="x", expand=False)
    header_frame.pack_propagate(False)
    hl = tk.Frame(header_frame, bg=T.POS_HEADER)
    hl.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=(14, 16))
    tk.Label(hl, text="Control de gastos", font=F_TITLE, bg=T.POS_HEADER, fg=T.WHITE).pack(anchor="w")
    tk.Label(
        hl,
        text="Registre egresos con fecha y hora automáticas · búsqueda por concepto o valor",
        font=F_SMALL,
        bg=T.POS_HEADER,
        fg=T.HEADER_TEXT_DIM,
    ).pack(anchor="w", pady=(4, 0))

    # Panel de fecha y hora
    def actualizar_tiempo():
        ahora = datetime.now()
        lbl_fecha.config(text=f"Fecha: {ahora.strftime('%d-%m-%Y')}")
        lbl_hora.config(text=f"Hora: {ahora.strftime('%H:%M:%S')}")
        fecha_var.set(ahora.strftime("%d-%m-%Y"))
        ventana.after(1000, actualizar_tiempo)

    panel_superior = tk.Frame(cuerpo, bg=T.BG_APP)
    panel_superior.pack(fill="x", pady=(12, 0), padx=16)

    time_card = tk.Frame(panel_superior, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
    time_card.pack(fill="x")
    bar_t = tk.Frame(time_card, bg=T.STAT_2, height=3)
    bar_t.pack(fill="x")
    time_container = tk.Frame(time_card, bg=T.BG_CARD)
    time_container.pack(pady=12, padx=16)

    lbl_fecha = tk.Label(time_container, text="", font=F_BODY_B, bg=T.BG_CARD, fg=T.TEXT)
    lbl_fecha.pack(side="left", padx=(0, 24))

    lbl_hora = tk.Label(time_container, text="", font=F_BODY_B, bg=T.BG_CARD, fg=T.TEXT_MUTED)
    lbl_hora.pack(side="left", padx=0)

    actualizar_tiempo()

    stats_frame = tk.Frame(cuerpo, bg=T.BG_APP)
    stats_frame.pack(fill="x", expand=False, pady=12, padx=16)

    stats_container = tk.Frame(stats_frame, bg=T.BG_APP)
    stats_container.pack(fill="x")

    def actualizar_stats_display():
        total_gastos, gastos_hoy_count, gastos_hoy_valor, total_registros = calcular_estadisticas_gastos()

        for widget in stats_container.winfo_children():
            widget.destroy()

        stats_data = [
            ("Total gastos", f"${total_gastos:,.0f}", T.STAT_1),
            ("Gastos hoy", f"${gastos_hoy_valor:,.0f}", T.STAT_3),
            ("Registros", str(total_registros), T.STAT_2),
            ("Registros hoy", str(gastos_hoy_count), T.STAT_4),
        ]

        for titulo, valor, accent in stats_data:
            card = tk.Frame(stats_container, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
            card.pack(side="left", padx=(0, 10), pady=2, fill="both", expand=True)
            tk.Frame(card, bg=accent, height=4).pack(fill="x")
            inner = tk.Frame(card, bg=T.BG_CARD)
            inner.pack(fill="both", expand=True, padx=12, pady=10)
            tk.Label(inner, text=titulo, font=F_SMALL, bg=T.BG_CARD, fg=T.TEXT_MUTED).pack(anchor="w")
            tk.Label(inner, text=valor, font=F_STAT, bg=T.BG_CARD, fg=T.TEXT).pack(anchor="w", pady=(2, 0))

    actualizar_stats_display()

    form_outer = tk.Frame(cuerpo, bg=T.BG_APP)
    form_outer.pack(fill="x", pady=(4, 0), padx=16)
    form_frame = tk.Frame(form_outer, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
    form_frame.pack(fill="x")
    tk.Frame(form_frame, bg=T.ACCENT, height=3).pack(fill="x")

    tk.Label(form_frame, text="Registrar gasto", font=F_HEAD, bg=T.BG_CARD, fg=T.TEXT).pack(anchor="w", padx=16, pady=(12, 4))

    form_container = tk.Frame(form_frame, bg=T.BG_CARD)
    form_container.pack(pady=(0, 12), padx=16, fill="x")

    row1 = tk.Frame(form_container, bg=T.BG_CARD)
    row1.pack(fill="x", pady=6)

    tk.Label(row1, text="Concepto", font=F_BODY_B, bg=T.BG_CARD, fg=T.TEXT).pack(side="left", padx=(0, 10))
    concepto_entry = tk.Entry(
        row1, textvariable=concepto_var, font=F_BODY, width=28, relief="flat", bd=0,
        highlightthickness=1, highlightbackground=T.INPUT_BORDER, highlightcolor=T.ACCENT,
    )
    concepto_entry.pack(side="left", padx=(0, 20), ipady=4)

    tk.Label(row1, text="Valor (COP)", font=F_BODY_B, bg=T.BG_CARD, fg=T.TEXT).pack(side="left", padx=(0, 10))
    valor_entry = tk.Entry(
        row1, textvariable=valor_var, font=F_BODY, width=16, relief="flat", bd=0,
        highlightthickness=1, highlightbackground=T.INPUT_BORDER, highlightcolor=T.ACCENT,
    )
    valor_entry.pack(side="left", ipady=4)

    row2 = tk.Frame(form_container, bg=T.BG_CARD)
    row2.pack(fill="x", pady=10)

    tk.Label(row2, text="Fecha", font=F_BODY_B, bg=T.BG_CARD, fg=T.TEXT).pack(side="left", padx=(0, 10))
    fecha_entry = tk.Entry(
        row2, textvariable=fecha_var, font=F_BODY, width=14, state="readonly", readonlybackground=T.INPUT_BG_ALT,
        relief="flat", bd=0, highlightthickness=1, highlightbackground=T.INPUT_BORDER,
    )
    fecha_entry.pack(side="left", padx=(0, 24), ipady=4)

    # Botones de acción
    def ingresar_gasto():
        if not concepto_var.get().strip():
            messagebox.showwarning("Campo vacío", "Ingrese un concepto para el gasto.", parent=ventana)
            concepto_entry.focus()
            return
        
        try:
            valor = float(valor_var.get().replace(',', '').replace('$', ''))
            if valor <= 0:
                raise ValueError("El valor debe ser mayor a 0")
        except ValueError:
            messagebox.showwarning("Valor inválido", "Ingrese un valor numérico válido mayor a cero.", parent=ventana)
            valor_entry.focus()
            return

        # Agregar gasto a la base de datos
        hora_actual = datetime.now().strftime("%H:%M:%S")
        concepto_txt = concepto_var.get().strip()
        if agregar_gasto_db(concepto_txt, valor, fecha_var.get(), hora_actual):
            # Actualizar tabla y estadísticas
            actualizar_tabla()
            actualizar_stats_display()
            
            # Limpiar campos
            concepto_var.set("")
            valor_var.set("")
            concepto_entry.focus()
            
            messagebox.showinfo(
                "Gasto registrado",
                f"Concepto: {concepto_txt}\nValor: ${valor:,.0f}",
                parent=ventana,
            )

    def eliminar_gasto():
        seleccionado = tabla.focus()
        if not seleccionado:
            messagebox.showwarning("Selección", "Seleccione un gasto en la tabla para eliminarlo.", parent=ventana)
            return
        
        respuesta = messagebox.askyesno(
            "Confirmar eliminación",
            "¿Eliminar este gasto? Esta acción no se puede deshacer.",
            parent=ventana,
        )
        if respuesta:
            # Obtener ID del gasto seleccionado
            valores = tabla.item(seleccionado)["values"]
            id_gasto = valores[0]  # El ID está en la primera columna
            
            if eliminar_gasto_db(id_gasto):
                actualizar_tabla()
                actualizar_stats_display()
                messagebox.showinfo("Eliminado", "Gasto eliminado correctamente.", parent=ventana)

    def modificar_gasto():
        seleccionado = tabla.focus()
        if not seleccionado:
            messagebox.showwarning("Selección", "Seleccione un gasto en la tabla para modificarlo.", parent=ventana)
            return
        
        # Obtener datos del gasto seleccionado
        valores = tabla.item(seleccionado)["values"]
        id_gasto = valores[0]
        
        # Ventana de modificación
        ventana_mod = tk.Toplevel(ventana)
        ventana_mod.title("Modificar gasto · VmPOS")
        ventana_mod.configure(bg=T.BG_APP)
        ventana_mod.resizable(False, False)
        ventana_mod.transient(ventana)
        ventana_mod.grab_set()
        centrar_ventana(ventana_mod, 450, 300, ventana)

        hdr_m = tk.Frame(ventana_mod, bg=T.POS_HEADER, height=52)
        hdr_m.pack(fill="x")
        hdr_m.pack_propagate(False)
        tk.Label(hdr_m, text="Modificar gasto", font=F_HEAD, bg=T.POS_HEADER, fg=T.WHITE).pack(
            side=tk.LEFT, padx=16, pady=12
        )
        
        # Variables para modificación
        mod_concepto = tk.StringVar(value=valores[1])
        mod_valor = tk.StringVar(value=str(float(valores[2].replace('$', '').replace(',', ''))))
        
        # Campos de modificación
        campos_frame = tk.Frame(ventana_mod, bg=T.BG_APP)
        campos_frame.pack(pady=16, padx=20, fill="x")

        tk.Label(campos_frame, text="Concepto", font=F_BODY_B, bg=T.BG_APP, fg=T.TEXT).pack(anchor="w", pady=(0, 4))
        tk.Entry(campos_frame, textvariable=mod_concepto, font=F_BODY, width=42, relief="flat", highlightthickness=1,
                 highlightbackground=T.INPUT_BORDER).pack(fill="x", pady=(0, 12), ipady=4)

        tk.Label(campos_frame, text="Valor (COP)", font=F_BODY_B, bg=T.BG_APP, fg=T.TEXT).pack(anchor="w", pady=(0, 4))
        tk.Entry(campos_frame, textvariable=mod_valor, font=F_BODY, width=42, relief="flat", highlightthickness=1,
                 highlightbackground=T.INPUT_BORDER).pack(fill="x", pady=(0, 8), ipady=4)
        
        def guardar_cambios():
            try:
                nuevo_valor = float(mod_valor.get().replace(',', '').replace('$', ''))
                if nuevo_valor <= 0:
                    raise ValueError("El valor debe ser mayor a 0")
                
                if modificar_gasto_db(id_gasto, mod_concepto.get().strip(), nuevo_valor):
                    actualizar_tabla()
                    actualizar_stats_display()
                    ventana_mod.destroy()
                    messagebox.showinfo("Modificado", "Gasto actualizado correctamente.", parent=ventana)
                
            except ValueError as e:
                messagebox.showwarning("Valor inválido", "Ingrese un valor numérico válido.", parent=ventana_mod)

        btn_frame = tk.Frame(ventana_mod, bg=T.BG_APP)
        btn_frame.pack(pady=(8, 16))

        tk.Button(
            btn_frame, text="Guardar", command=guardar_cambios,
            bg=T.STAT_3, fg=T.WHITE, font=F_BODY_B, padx=18, pady=8, relief="flat", cursor="hand2",
            activebackground=T.POS_BTN_GO_HOVER, activeforeground=T.WHITE,
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            btn_frame, text="Cancelar", command=ventana_mod.destroy,
            bg=T.POS_BTN_ALT, fg=T.WHITE, font=F_BODY_B, padx=18, pady=8, relief="flat", cursor="hand2",
            activebackground=T.TEXT_MUTED, activeforeground=T.WHITE,
        ).pack(side="left", padx=8)

    buttons_frame = tk.Frame(row2, bg=T.BG_CARD)
    buttons_frame.pack(side="right")

    btn_ingresar = tk.Button(
        buttons_frame, text="Ingresar gasto", command=ingresar_gasto,
        bg=T.STAT_3, fg=T.WHITE, font=F_BODY_B, padx=14, pady=8, relief="flat", cursor="hand2",
        activebackground=T.POS_BTN_GO_HOVER, activeforeground=T.WHITE,
    )
    btn_ingresar.pack(side="left", padx=4)

    btn_eliminar = tk.Button(
        buttons_frame, text="Eliminar", command=eliminar_gasto,
        bg=T.DANGER, fg=T.WHITE, font=F_BODY_B, padx=14, pady=8, relief="flat", cursor="hand2",
        activebackground="#b91c1c", activeforeground=T.WHITE,
    )
    btn_eliminar.pack(side="left", padx=4)

    btn_modificar = tk.Button(
        buttons_frame, text="Modificar", command=modificar_gasto,
        bg=T.STAT_1, fg=T.WHITE, font=F_BODY_B, padx=14, pady=8, relief="flat", cursor="hand2",
        activebackground="#0284c7", activeforeground=T.WHITE,
    )
    btn_modificar.pack(side="left", padx=4)

    search_outer = tk.Frame(cuerpo, bg=T.BG_APP)
    search_outer.pack(fill="x", pady=(8, 0), padx=16)
    search_frame = tk.Frame(search_outer, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
    search_frame.pack(fill="x")
    tk.Frame(search_frame, bg=T.STAT_1, height=3).pack(fill="x")
    search_container = tk.Frame(search_frame, bg=T.BG_CARD)
    search_container.pack(fill="x", padx=12, pady=10)

    tk.Label(search_container, text="Buscar", font=F_BODY_B, bg=T.BG_CARD, fg=T.TEXT).pack(side="left", padx=(0, 10))

    search_var = tk.StringVar()
    search_entry = tk.Entry(
        search_container, textvariable=search_var, font=F_BODY, width=32, relief="flat", bd=0,
        highlightthickness=1, highlightbackground=T.INPUT_BORDER,
    )
    search_entry.pack(side="left", padx=(0, 10), ipady=4)

    def buscar_gastos():
        busqueda = search_var.get().lower()
        if not busqueda:
            actualizar_tabla()
            return
        
        # Filtrar gastos en la base de datos
        try:
            with sqlite3.connect(ruta_db) as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT * FROM gastos
                    WHERE LOWER(concepto) LIKE ? OR CAST(valor AS TEXT) LIKE ? OR fecha LIKE ?
                    ORDER BY fecha_registro DESC
                    """,
                    (f"%{busqueda}%", f"%{busqueda}%", f"%{busqueda}%"),
                )
                gastos_filtrados = cur.fetchall()
            
            tabla.delete(*tabla.get_children())
            for gasto in gastos_filtrados:
                tag = "even" if len(tabla.get_children()) % 2 == 0 else "odd"
                tabla.insert("", "end", values=(
                    gasto[0],  # id_gasto
                    gasto[1],  # concepto
                    f"${gasto[2]:,.0f}",  # valor
                    gasto[3],  # fecha
                    gasto[4]   # hora
                ), tags=(tag,))
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al buscar gastos: {e}", parent=ventana)

    tk.Button(
        search_container, text="Buscar", command=buscar_gastos,
        bg=T.STAT_2, fg=T.WHITE, font=F_BODY_B, padx=14, pady=6, relief="flat", cursor="hand2",
        activebackground="#7c3aed", activeforeground=T.WHITE,
    ).pack(side="left", padx=4)

    tk.Button(
        search_container, text="Mostrar todos", command=lambda: [search_var.set(""), actualizar_tabla()],
        bg=T.POS_BTN_ALT, fg=T.WHITE, font=F_BODY_B, padx=14, pady=6, relief="flat", cursor="hand2",
        activebackground=T.TEXT_MUTED, activeforeground=T.WHITE,
    ).pack(side="left", padx=4)

    table_outer = tk.Frame(cuerpo, bg=T.BG_APP)
    table_outer.pack(fill="both", expand=True, padx=16, pady=(12, 16))

    tk.Label(table_outer, text="Historial de gastos", font=F_HEAD, bg=T.BG_APP, fg=T.TEXT).pack(anchor="w", pady=(0, 8))

    table_wrap = tk.Frame(table_outer, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
    table_wrap.pack(fill="both", expand=True)
    tk.Frame(table_wrap, bg=T.POS_HEADER, height=3).pack(fill="x")
    table_container = tk.Frame(table_wrap, bg=T.BG_CARD)
    table_container.pack(fill="both", expand=True, padx=4, pady=4)

    style = ttk.Style()
    style_ttk_treeview_pos(style, T.BG_APP)

    columnas = ("ID", "Concepto", "Valor", "Fecha", "Hora")
    tabla = ttk.Treeview(table_container, columns=columnas, show="headings", height=10)

    # Configurar columnas
    widths = [60, 300, 120, 100, 80]
    for i, col in enumerate(columnas):
        tabla.heading(col, text=col)
        tabla.column(col, width=widths[i], anchor="center")

    # Scrollbars
    v_scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=tabla.yview)
    h_scrollbar = ttk.Scrollbar(table_container, orient="horizontal", command=tabla.xview)
    tabla.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

    # Grid para mejor organización
    tabla.grid(row=0, column=0, sticky="nsew")
    v_scrollbar.grid(row=0, column=1, sticky="ns")
    h_scrollbar.grid(row=1, column=0, sticky="ew")
    
    # Configurar el grid para que se expanda
    table_container.grid_rowconfigure(0, weight=1)
    table_container.grid_columnconfigure(0, weight=1)

    # Función para desplazamiento con el ratón
    def on_mousewheel(event):
        tabla.yview_scroll(int(-1*(event.delta/120)), "units")
    
    # Vincular el evento de la rueda del ratón a la tabla
    tabla.bind("<MouseWheel>", on_mousewheel)
    
    # También vincular el evento a la barra de desplazamiento vertical
    v_scrollbar.bind("<MouseWheel>", on_mousewheel)
    
    # Para Linux, necesitamos bindings adicionales
    tabla.bind("<Button-4>", lambda e: tabla.yview_scroll(-1, "units"))
    tabla.bind("<Button-5>", lambda e: tabla.yview_scroll(1, "units"))
    v_scrollbar.bind("<Button-4>", lambda e: tabla.yview_scroll(-1, "units"))
    v_scrollbar.bind("<Button-5>", lambda e: tabla.yview_scroll(1, "units"))

    def actualizar_tabla():
        # Limpiar tabla
        tabla.delete(*tabla.get_children())
        
        # Obtener gastos de la base de datos
        gastos = obtener_gastos()
        
        # Agregar gastos a la tabla
        for gasto in gastos:
            tag = "even" if len(tabla.get_children()) % 2 == 0 else "odd"
            tabla.insert("", "end", values=(
                gasto[0],  # id_gasto
                gasto[1],  # concepto
                f"${gasto[2]:,.0f}",  # valor
                gasto[3],  # fecha
                gasto[4]   # hora
            ), tags=(tag,))
        
        # Configurar colores alternos
        tabla.tag_configure("even", background=T.BG_SUBTLE)
        tabla.tag_configure("odd", background=T.BG_CARD)

    # Cargar datos iniciales
    actualizar_tabla()

    tk.Label(
        footer_frame,
        text="VmPOS · Gastos",
        font=F_SMALL,
        bg=T.FOOTER,
        fg=T.HEADER_TEXT_DIM,
    ).pack(expand=True, pady=14)

    # Enfocar el campo concepto al inicio
    concepto_entry.focus()

    # 🎯 Eventos de teclado
    def keyboard_shortcuts(event):
        if event.state & 4:  # Ctrl presionado
            key = event.keysym.lower()
            if key == 'n':  # Ctrl+N para nuevo gasto
                concepto_entry.focus()
            elif key == 'f':  # Ctrl+F para buscar
                search_entry.focus()
            elif key == 's':  # Ctrl+S para guardar
                ingresar_gasto()

    # Vincular Enter para ingresar gasto
    def on_enter(event):
        if event.widget == valor_entry:
            ingresar_gasto()

    valor_entry.bind('<Return>', on_enter)
    concepto_entry.bind('<Return>', lambda e: valor_entry.focus())

    ventana.bind("<KeyPress>", keyboard_shortcuts)
    ventana.focus_set()

    modulo_scroll_finalizar(cuerpo)

    # Cerrar ventana
    def on_closing():
        ventana.destroy()

    ventana.protocol("WM_DELETE_WINDOW", on_closing)
    if parent is None:
        ventana.mainloop()

# Ejecutar si es llamado directamente
if __name__ == "__main__":
    iniciar_gastos()