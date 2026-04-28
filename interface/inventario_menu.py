# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import re
import sqlite3

from paths import ventas_db_path
from layout_responsive import centrar_ventana, crear_cuerpo_modulo_scroll, modulo_scroll_finalizar, bind_reflow_pack
from ui_theme import T, F_TITLE, F_HEAD, F_BODY, F_BODY_B, F_SMALL, F_BTN, style_ttk_treeview_pos

ruta_db = ventas_db_path()

TIPO_PRODUCTO = "producto"
TIPO_SERVICIO = "servicio"


def _normalizar_tipo(s):
    t = (s or TIPO_PRODUCTO).strip().lower()
    return TIPO_SERVICIO if t == TIPO_SERVICIO else TIPO_PRODUCTO


def _etiqueta_tipo(t):
    return "Servicio" if _normalizar_tipo(t) == TIPO_SERVICIO else "Producto"


# 💵 Formato de pesos colombianos
def formato_peso(valor):
    if valor is None or valor == '':
        return "$0 COP"
    return f"${valor:,.0f} COP"

def limpiar_precio(texto):
    """Limpia una cadena de texto para extraer un valor numérico flotante."""
    texto = str(texto).replace("$", "").replace("COP", "").replace(",", "").strip()
    try:
        return float(texto)
    except ValueError:
        return 0.0

# 🧩 Funciones de base de datos - CORREGIDAS
def conectar_db():
    """Establece conexión con la base de datos y crea las tablas si no existen"""
    try:
        conn = sqlite3.connect(ruta_db)
        cursor = conn.cursor()
        
        # Crear tabla productos si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                precio REAL DEFAULT 0,
                costo REAL DEFAULT 0,
                stock INTEGER DEFAULT 0,
                tipo TEXT DEFAULT 'producto',
                referencia TEXT,
                categoria TEXT
            )
        """)
        cursor.execute("PRAGMA table_info(productos)")
        col_names = [r[1] for r in cursor.fetchall()]
        if "tipo" not in col_names:
            cursor.execute("ALTER TABLE productos ADD COLUMN tipo TEXT DEFAULT 'producto'")
        if "referencia" not in col_names:
            cursor.execute("ALTER TABLE productos ADD COLUMN referencia TEXT")
        if "categoria" not in col_names:
            cursor.execute("ALTER TABLE productos ADD COLUMN categoria TEXT")

        # Crear tabla ventas si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_venta TEXT NOT NULL,
                hora_venta TEXT NOT NULL,
                documento_cliente TEXT,
                total_venta REAL NOT NULL
            )
        """)
        
        # Crear tabla detalle_ventas si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detalle_ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_venta INTEGER NOT NULL,
                codigo_producto TEXT NOT NULL,
                nombre_producto TEXT NOT NULL,
                precio_unitario REAL NOT NULL,
                cantidad INTEGER NOT NULL,
                subtotal REAL NOT NULL,
                FOREIGN KEY (id_venta) REFERENCES ventas (id)
            )
        """)
        
        conn.commit()
        return conn
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        messagebox.showerror("Error de DB", f"No se pudo conectar a la base de datos: {e}")
        return None

def _siguiente_codigo_producto(conn):
    """Código numérico de 5 dígitos (excluye códigos tipo Sxxxxx)."""
    c = conn.cursor()
    c.execute("SELECT codigo, COALESCE(tipo, 'producto') FROM productos")
    m = 0
    for cod, t in c.fetchall():
        s = str(cod).strip()
        if s.isdigit():
            m = max(m, int(s))
    return str(m + 1).zfill(5)


def _siguiente_codigo_servicio(conn):
    c = conn.cursor()
    c.execute("SELECT codigo FROM productos WHERE COALESCE(tipo, 'producto') = ?", (TIPO_SERVICIO,))
    m = 0
    for (cod,) in c.fetchall():
        mm = re.match(r"^S(\d+)$", str(cod), re.IGNORECASE)
        if mm:
            m = max(m, int(mm.group(1)))
    return f"S{str(m + 1).zfill(5)}"


def _referencia_servicio_existe(conn, ref, exclude_id=None):
    r = (ref or "").strip().lower()
    if not r:
        return False
    c = conn.cursor()
    if exclude_id is not None:
        c.execute(
            """
            SELECT 1 FROM productos
            WHERE LOWER(TRIM(COALESCE(referencia, ''))) = ?
              AND COALESCE(tipo, 'producto') = ?
              AND id != ?
            """,
            (r, TIPO_SERVICIO, exclude_id),
        )
    else:
        c.execute(
            """
            SELECT 1 FROM productos
            WHERE LOWER(TRIM(COALESCE(referencia, ''))) = ?
              AND COALESCE(tipo, 'producto') = ?
            """,
            (r, TIPO_SERVICIO),
        )
    return c.fetchone() is not None


def insertar_producto(nombre, precio_venta, precio_compra, stock_inicial, categoria="", parent_win=None):
    """Producto: código generado, sin referencia de servicio."""
    nombre = (nombre or "").strip()
    if not nombre:
        messagebox.showwarning("Datos", "El nombre del producto es obligatorio.", parent=parent_win)
        return False
    try:
        stock_inicial = int(stock_inicial) if stock_inicial is not None else 0
    except (TypeError, ValueError):
        messagebox.showerror("Datos", "La cantidad en stock debe ser un número entero.", parent=parent_win)
        return False
    try:
        conn = conectar_db()
        if not conn:
            return False
        codigo = _siguiente_codigo_producto(conn)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO productos (codigo, nombre, precio, costo, stock, tipo, referencia, categoria)
            VALUES (?, ?, ?, ?, ?, ?, NULL, ?)
            """,
            (
                codigo,
                nombre,
                float(precio_venta or 0),
                float(precio_compra or 0),
                max(0, stock_inicial),
                TIPO_PRODUCTO,
                (categoria or "").strip(),
            ),
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo guardar el producto:\n{e}", parent=parent_win)
        return False


def insertar_servicio(nombre, referencia, precio, parent_win=None):
    """Servicio: código Sxxxxx autogenerado; referencia visible y única por servicio."""
    nombre = (nombre or "").strip()
    ref = (referencia or "").strip()
    if not nombre or not ref:
        messagebox.showwarning("Datos", "Nombre y referencia del servicio son obligatorios.", parent=parent_win)
        return False
    try:
        conn = conectar_db()
        if not conn:
            return False
        if _referencia_servicio_existe(conn, ref, None):
            messagebox.showerror("Duplicado", f"Ya existe un servicio con la referencia «{ref}».", parent=parent_win)
            conn.close()
            return False
        codigo = _siguiente_codigo_servicio(conn)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO productos (codigo, nombre, precio, costo, stock, tipo, referencia)
            VALUES (?, ?, ?, 0, 0, ?, ?)
            """,
            (codigo, nombre, float(precio or 0), TIPO_SERVICIO, ref),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "No se pudo generar un código interno único. Intente de nuevo.", parent=parent_win)
        return False
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo guardar el servicio:\n{e}", parent=parent_win)
        return False

def actualizar_producto(
    id_producto,
    nombre,
    precio,
    costo,
    stock,
    tipo=TIPO_PRODUCTO,
    referencia=None,
    categoria="",
    parent_win=None,
):
    """Actualiza producto (compra/venta/stock) o servicio (nombre, referencia, precio)."""
    try:
        conn = conectar_db()
        if not conn:
            return False

        cursor = conn.cursor()
        t = _normalizar_tipo(tipo)
        if t == TIPO_SERVICIO:
            ref = (referencia or "").strip()
            if not ref:
                messagebox.showwarning("Datos", "La referencia del servicio es obligatoria.", parent=parent_win)
                conn.close()
                return False
            if _referencia_servicio_existe(conn, ref, exclude_id=id_producto):
                messagebox.showerror("Duplicado", f"Ya existe otro servicio con la referencia «{ref}».", parent=parent_win)
                conn.close()
                return False
            cursor.execute(
                """
                UPDATE productos
                SET nombre = ?, precio = ?, costo = 0, stock = 0, tipo = ?, referencia = ?, categoria = ?
                WHERE id = ?
                """,
                (nombre, float(precio or 0), t, ref, (categoria or "").strip(), id_producto),
            )
        else:
            cursor.execute(
                """
                UPDATE productos
                SET nombre = ?, precio = ?, costo = ?, stock = ?, tipo = ?, referencia = NULL, categoria = ?
                WHERE id = ?
                """,
                (
                    nombre,
                    float(precio or 0),
                    float(costo or 0),
                    int(stock or 0),
                    t,
                    (categoria or "").strip(),
                    id_producto,
                ),
            )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Error al actualizar: {e}", parent=parent_win)
        return False

def eliminar_producto(id_producto):
    """Elimina un producto de la base de datos"""
    try:
        conn = conectar_db()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute("DELETE FROM productos WHERE id = ?", (id_producto,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Error al eliminar producto: {e}")
        return False

def obtener_productos():
    """Filas: id, codigo, nombre, precio, costo, stock, tipo, referencia, categoria."""
    try:
        conn = conectar_db()
        if not conn:
            return []

        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT id, codigo, nombre, precio, costo, stock,
                       COALESCE(tipo, 'producto'),
                       TRIM(COALESCE(referencia, '')),
                       TRIM(COALESCE(categoria, ''))
                FROM productos
                """
            )
        except sqlite3.OperationalError:
            cursor.execute(
                "SELECT id, codigo, nombre, precio, costo, stock, COALESCE(tipo, 'producto') FROM productos"
            )
            productos = []
            for r in cursor.fetchall():
                productos.append(r + ("", ""))
            conn.close()
            return productos
        productos = cursor.fetchall()
        conn.close()
        return productos
    except Exception as e:
        messagebox.showerror("Error", f"Error al obtener productos: {e}")
        return []

# Interfaz principal
def iniciar_inventario(parent=None):
    if parent is not None:
        ventana = tk.Toplevel(parent)
        try:
            ventana.transient(parent)
        except tk.TclError:
            pass
    else:
        ventana = tk.Tk()
    ventana.title("Inventario - VmPOS")
    if parent is not None:
        from navegacion_ventanas import instalar_barra_volver
        instalar_barra_volver(ventana, parent)
    else:
        from layout_responsive import configurar_ventana_modulo
        configurar_ventana_modulo(ventana, min_w=900, min_h=480)
    ventana.resizable(True, True)
    ventana.configure(bg=T.BG_APP)

    # Verificar conexión a la base de datos al inicio
    conn_test = conectar_db()
    if not conn_test:
        messagebox.showerror("Error Crítico", "No se puede conectar a la base de datos. La aplicación se cerrará.")
        try:
            ventana.destroy()
        except tk.TclError:
            pass
        if parent is not None:
            try:
                parent.wm_deiconify()
                parent.lift()
                parent.focus_force()
            except tk.TclError:
                pass
        return
    conn_test.close()

    # Pie: discreto, alineado al tema VmPOS
    footer = tk.Frame(ventana, bg=T.FOOTER, height=40)
    footer.pack_propagate(False)
    footer_left = tk.Frame(footer, bg=T.FOOTER)
    footer_left.pack(side=tk.LEFT, padx=16, pady=8)
    footer_right = tk.Frame(footer, bg=T.FOOTER)
    footer_right.pack(side=tk.RIGHT, padx=16, pady=8)
    tk.Label(footer_left, text="Variedades Marce \u00b7 Puerto Colombia", font=F_SMALL, bg=T.FOOTER, fg=T.HEADER_TEXT_DIM).pack(anchor="w")
    tk.Label(footer_right, text="VmPOS · inventario", font=F_SMALL, bg=T.FOOTER, fg=T.HEADER_TEXT_DIM).pack(anchor="e")
    footer.pack(side=tk.BOTTOM, fill=tk.X)

    cuerpo = crear_cuerpo_modulo_scroll(ventana, bg=T.BG_APP)

    # Cabecera: slate (mismo criterio que ventas)
    header_frame = tk.Frame(cuerpo, bg=T.POS_HEADER, height=78)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)

    header_left = tk.Frame(header_frame, bg=T.POS_HEADER)
    header_left.pack(side="left", fill="y", padx=20)

    tk.Label(
        header_left,
        text="Inventario",
        font=F_TITLE,
        bg=T.POS_HEADER,
        fg=T.WHITE,
    ).pack(anchor="w", pady=(16, 0))
    tk.Label(
        header_left,
        text="Catálogo de productos y servicios · costos, precios y existencias",
        font=F_SMALL,
        bg=T.POS_HEADER,
        fg=T.HEADER_TEXT_DIM,
    ).pack(anchor="w", pady=(0, 12))

    header_right = tk.Frame(header_frame, bg=T.POS_HEADER)
    header_right.pack(side="right", fill="y", padx=20)

    lbl_fecha = tk.Label(header_right, text="", font=F_SMALL, bg=T.POS_HEADER, fg=T.HEADER_TEXT_DIM)
    lbl_fecha.pack(anchor="e", pady=(18, 2))

    lbl_hora = tk.Label(header_right, text="", font=F_SMALL, bg=T.POS_HEADER, fg=T.WHITE)
    lbl_hora.pack(anchor="e", pady=(0, 14))

    def actualizar_tiempo():
        ahora = datetime.now()
        lbl_fecha.config(text=ahora.strftime("%d %b %Y"))
        lbl_hora.config(text=ahora.strftime("%H:%M:%S"))
        ventana.after(1000, actualizar_tiempo)

    actualizar_tiempo()

    main_content = tk.Frame(cuerpo, bg=T.BG_APP)
    main_content.pack(fill="both", expand=True, padx=16, pady=12)

    var_filtro_tipo = tk.StringVar(value="Todos")
    var_busca = tk.StringVar(value="")
    var_stats = tk.StringVar(value="")

    def _filtro_activo():
        v = (var_filtro_tipo.get() or "Todos").strip()
        if v == "Solo productos":
            return TIPO_PRODUCTO
        if v == "Solo servicios":
            return TIPO_SERVICIO
        return None  # Todos

    def cargar_tabla():
        """Carga la tabla con filtro por categoría y búsqueda por código, nombre o referencia."""
        try:
            if not (ventana.winfo_exists() and tabla.winfo_exists()):
                return
            for item in tabla.get_children():
                tabla.delete(item)
            productos = obtener_productos()
            ft = _filtro_activo()
            q = (var_busca.get() or "").strip().lower()
            mostrados = 0
            for row in productos:
                id_, codigo, nombre, precio, costo, stock, raw_tipo, referencia, categoria = row
                t = _normalizar_tipo(raw_tipo)
                ref = (referencia or "").strip()
                cat = (categoria or "").strip()
                if ft is not None and t != ft:
                    continue
                if q and q not in f"{codigo} {nombre} {ref} {cat}".lower():
                    continue
                ref_show = ref if t == TIPO_SERVICIO else "—"
                stock_show = "—" if t == TIPO_SERVICIO else stock
                pc_show = "—" if t == TIPO_SERVICIO else formato_peso(costo)
                tabla.insert(
                    "",
                    "end",
                    values=(
                        id_,
                        codigo,
                        ref_show,
                        nombre,
                        cat or "—",
                        _etiqueta_tipo(t),
                        formato_peso(precio),
                        pc_show,
                        stock_show,
                    ),
                )
                mostrados += 1
            n_tot = len(productos)
            var_stats.set(f"Mostrando {mostrados} de {n_tot} ítems en catálogo")
        except tk.TclError:
            # La ventana/tabla pudo cerrarse mientras llegaba un evento global de teclado.
            return
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar tabla: {e}")

    def _btn_hover(btn, normal, hover):
        def on_enter(_e):
            btn.config(bg=hover)

        def on_leave(_e):
            btn.config(bg=normal)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

    def btn_barra_lateral(parent, texto, bg, hover, comando):
        """Botón compacto para la barra lateral (tema VmPOS)."""
        f = tk.Frame(parent, bg=T.BG_CARD)
        f.pack(fill=tk.X, pady=3, padx=0)
        b = tk.Button(
            f,
            text=texto,
            font=F_BODY_B,
            bg=bg,
            fg=T.WHITE,
            bd=0,
            pady=9,
            cursor="hand2",
            command=comando,
            relief="flat",
            anchor="w",
            padx=14,
            activebackground=hover,
            activeforeground=T.WHITE,
        )
        b.pack(fill=tk.X)
        _btn_hover(b, bg, hover)
        return b

    def btn_accion_secundario(parent, texto, comando):
        f = tk.Frame(parent, bg=T.BG_APP)
        f.pack(pady=8, fill=tk.X, padx=4)
        b = tk.Button(
            f,
            text=texto,
            font=F_BODY_B,
            bg=T.POS_BTN_ALT,
            fg=T.WHITE,
            bd=0,
            pady=10,
            command=comando,
            relief="flat",
            cursor="hand2",
            activebackground="#334155",
            activeforeground=T.WHITE,
        )
        b.pack(fill=tk.X)
        _btn_hover(b, T.POS_BTN_ALT, "#334155")
        return b

    def abrir_ventana_registro():
        ventana_registro = tk.Toplevel(ventana)
        ventana_registro.title("Nuevo ítem")
        ventana_registro.configure(bg=T.BG_APP)
        ventana_registro.transient(ventana)
        ventana_registro.grab_set()
        centrar_ventana(ventana_registro, 430, 520, ventana)

        cap = tk.Frame(ventana_registro, bg=T.BG_APP)
        cap.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        card = tk.Frame(cap, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            card, text="Alta en catálogo", font=F_HEAD, bg=T.BG_CARD, fg=T.POS_TEXT, anchor="w"
        ).pack(anchor="w", padx=20, pady=(18, 4))
        hint = tk.Label(
            card,
            text="Elija el tipo. El código interno lo asigna el sistema.",
            font=F_SMALL,
            bg=T.BG_CARD,
            fg=T.TEXT_MUTED,
            wraplength=380,
            justify=tk.LEFT,
        )
        hint.pack(anchor="w", padx=20, pady=(0, 8))

        top = tk.Frame(card, bg=T.BG_CARD)
        top.pack(fill=tk.X, padx=20, pady=4)
        tk.Label(top, text="Tipo de ítem:", bg=T.BG_CARD, fg=T.POS_TEXT, font=F_BODY_B).pack(side=tk.LEFT, padx=(0, 8))
        cb_tipo = ttk.Combobox(
            top, width=36, state="readonly",
            values=("Producto (inventariable)", "Servicio"),
            font=F_BODY,
        )
        cb_tipo.set("Producto (inventariable)")
        cb_tipo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        fr_prod = tk.Frame(card, bg=T.BG_CARD)
        fr_srv = tk.Frame(card, bg=T.BG_CARD)
        e_prod = {}
        e_srv = {}

        r = 0
        for lbl, key in [
            ("Nombre", "nombre"),
            ("Categoría", "categoria"),
            ("Precio de compra", "p_compra"),
            ("Precio de venta", "p_venta"),
            ("Cantidad a ingresar al stock", "stock_n"),
        ]:
            tk.Label(fr_prod, text=lbl + ":", bg=T.BG_CARD, fg=T.POS_TEXT, font=F_BODY).grid(
                row=r, column=0, padx=(0, 10), pady=6, sticky="w"
            )
            w = tk.Entry(
                fr_prod, width=30, font=F_BODY, bg=T.INPUT_BG, fg=T.POS_TEXT,
                relief=tk.FLAT, highlightthickness=1, highlightbackground=T.INPUT_BORDER,
            )
            w.grid(row=r, column=1, padx=0, pady=6, sticky="ew")
            fr_prod.columnconfigure(1, weight=1)
            e_prod[key] = w
            r += 1

        r = 0
        for lbl, key in [("Nombre", "nombre_s"), ("Referencia", "referencia"), ("Precio del servicio", "precio_s")]:
            tk.Label(fr_srv, text=lbl + ":", bg=T.BG_CARD, fg=T.POS_TEXT, font=F_BODY).grid(
                row=r, column=0, padx=(0, 10), pady=6, sticky="w"
            )
            w = tk.Entry(
                fr_srv, width=30, font=F_BODY, bg=T.INPUT_BG, fg=T.POS_TEXT,
                relief=tk.FLAT, highlightthickness=1, highlightbackground=T.INPUT_BORDER,
            )
            w.grid(row=r, column=1, padx=0, pady=6, sticky="ew")
            fr_srv.columnconfigure(1, weight=1)
            e_srv[key] = w
            r += 1

        def _mostrar_tipo(_e=None):
            s = (cb_tipo.get() or "").strip().lower()
            if s == "servicio":
                fr_prod.pack_forget()
                fr_srv.pack(fill=tk.X, pady=8, padx=20)
                hint.config(
                    text="Servicio: use una referencia única (ej. copia A4, recarga 10k). Código interno: S00…"
                )
            else:
                fr_srv.pack_forget()
                fr_prod.pack(fill=tk.X, pady=8, padx=20)
                hint.config(
                    text="Producto: el código de barras o interno se genera solo. Indique compra, venta y unidades iniciales."
                )

        cb_tipo.bind("<<ComboboxSelected>>", _mostrar_tipo)

        acciones = tk.Frame(card, bg=T.BG_CARD)
        acciones.pack(fill=tk.X, padx=20, pady=(8, 20))
        f_btn = tk.Frame(acciones, bg=T.BG_CARD)
        f_btn.pack(fill=tk.X)

        def registrar():
            es_srv = (cb_tipo.get() or "").strip().lower() == "servicio"
            if es_srv:
                try:
                    pr = float(e_srv["precio_s"].get().replace(",", ".") or 0)
                except ValueError:
                    messagebox.showerror("Datos", "Precio del servicio no válido.", parent=ventana_registro)
                    return
                ok = insertar_servicio(
                    e_srv["nombre_s"].get().strip(),
                    e_srv["referencia"].get().strip(),
                    pr,
                    parent_win=ventana_registro,
                )
            else:
                try:
                    st = int(e_prod["stock_n"].get().strip() or 0)
                except ValueError:
                    messagebox.showerror("Datos", "La cantidad en stock debe ser un número entero.", parent=ventana_registro)
                    return
                try:
                    pc = float(e_prod["p_compra"].get().replace(",", ".") or 0)
                    pv = float(e_prod["p_venta"].get().replace(",", ".") or 0)
                except ValueError:
                    messagebox.showerror("Datos", "Precio de compra o venta no válido.", parent=ventana_registro)
                    return
                ok = insertar_producto(
                    e_prod["nombre"].get().strip(),
                    pv,
                    pc,
                    st,
                    e_prod["categoria"].get().strip(),
                    parent_win=ventana_registro,
                )
            if ok:
                messagebox.showinfo("Listo", "Registro guardado correctamente.", parent=ventana_registro)
                ventana_registro.destroy()
                cargar_tabla()

        b_g = tk.Button(
            f_btn, text="Guardar", font=F_BTN, bg=T.POS_BTN_GO, fg=T.WHITE, bd=0, pady=10,
            relief=tk.FLAT, cursor="hand2", command=registrar, activebackground=T.POS_BTN_GO_HOVER, activeforeground=T.WHITE
        )
        b_g.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        _btn_hover(b_g, T.POS_BTN_GO, T.POS_BTN_GO_HOVER)
        b_c = tk.Button(
            f_btn, text="Cancelar", font=F_BODY_B, bg=T.POS_BTN_ALT, fg=T.WHITE, bd=0, pady=10,
            relief=tk.FLAT, cursor="hand2", command=ventana_registro.destroy, activebackground="#334155", activeforeground=T.WHITE
        )
        b_c.pack(side=tk.LEFT, fill=tk.X, expand=True)
        _btn_hover(b_c, T.POS_BTN_ALT, "#334155")
        _mostrar_tipo()
        e_prod["nombre"].focus()

    def editar_producto():
        seleccionado = tabla.focus()
        if not seleccionado:
            messagebox.showwarning("Aviso", "Selecciona un ítem de la lista para editar.")
            return

        valores = tabla.item(seleccionado)["values"]
        id_producto = valores[0]
        codigo = valores[1]
        ref_tab = str(valores[2])
        nombre = valores[3]
        categoria_tab = str(valores[4])
        tipo_lab = str(valores[5])
        precio_val = limpiar_precio(valores[6])
        costo_val = limpiar_precio(valores[7]) if str(valores[7]) != "—" else 0.0
        stock_raw = valores[8]
        es_srv = tipo_lab.strip().lower() == "servicio"
        stock_val = 0 if str(stock_raw) == "—" else stock_raw

        ventana_edicion = tk.Toplevel(ventana)
        ventana_edicion.title("Editar ítem")
        ventana_edicion.configure(bg=T.BG_APP)
        ventana_edicion.transient(ventana)
        ventana_edicion.grab_set()
        centrar_ventana(ventana_edicion, 430, 480, ventana)

        cap = tk.Frame(ventana_edicion, bg=T.BG_APP)
        cap.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)
        card = tk.Frame(cap, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True)

        tk.Label(card, text="Editar catálogo", font=F_HEAD, bg=T.BG_CARD, fg=T.POS_TEXT, anchor="w").pack(
            anchor="w", padx=20, pady=(18, 4)
        )
        tk.Label(
            card, text="El código interno no se modifica.", font=F_SMALL, bg=T.BG_CARD, fg=T.TEXT_MUTED
        ).pack(anchor="w", padx=20, pady=(0, 8))

        campos_frame = tk.Frame(card, bg=T.BG_CARD)
        campos_frame.pack(pady=8, padx=20, fill=tk.X)

        row = 0
        tk.Label(campos_frame, text="Código interno:", bg=T.BG_CARD, fg=T.POS_TEXT, font=F_BODY).grid(
            row=row, column=0, padx=(0, 10), pady=6, sticky="w"
        )
        e_cod = tk.Entry(
            campos_frame, width=30, font=F_BODY, bg=T.INPUT_BG_ALT, fg=T.POS_TEXT,
            relief=tk.FLAT, highlightthickness=1, highlightbackground=T.INPUT_BORDER
        )
        e_cod.insert(0, str(codigo))
        e_cod.config(state="readonly")
        e_cod.grid(row=row, column=1, padx=0, pady=6, sticky="ew")
        campos_frame.columnconfigure(1, weight=1)
        row += 1

        entries = {"codigo": e_cod}

        if es_srv:
            tk.Label(campos_frame, text="Referencia:", bg=T.BG_CARD, fg=T.POS_TEXT, font=F_BODY).grid(
                row=row, column=0, padx=(0, 10), pady=6, sticky="w"
            )
            e_ref = tk.Entry(
                campos_frame, width=30, font=F_BODY, bg=T.INPUT_BG, fg=T.POS_TEXT,
                relief=tk.FLAT, highlightthickness=1, highlightbackground=T.INPUT_BORDER
            )
            e_ref.insert(0, ref_tab if ref_tab != "—" else "")
            e_ref.grid(row=row, column=1, padx=0, pady=6, sticky="ew")
            entries["referencia"] = e_ref
            row += 1
            for lbl, key, v0 in [("Nombre", "nombre", nombre), ("Precio del servicio", "precio", str(precio_val))]:
                tk.Label(campos_frame, text=lbl + ":", bg=T.BG_CARD, fg=T.POS_TEXT, font=F_BODY).grid(
                    row=row, column=0, padx=(0, 10), pady=6, sticky="w"
                )
                e = tk.Entry(
                    campos_frame, width=30, font=F_BODY, bg=T.INPUT_BG, fg=T.POS_TEXT,
                    relief=tk.FLAT, highlightthickness=1, highlightbackground=T.INPUT_BORDER
                )
                e.insert(0, v0)
                e.grid(row=row, column=1, padx=0, pady=6, sticky="ew")
                entries[key] = e
                row += 1
        else:
            for lbl, key, v0 in [
                ("Nombre", "nombre", nombre),
                ("Categoría", "categoria", "" if categoria_tab == "—" else categoria_tab),
                ("Precio de compra", "p_compra", str(costo_val)),
                ("Precio de venta", "p_venta", str(precio_val)),
                ("Stock actual", "stock", str(stock_val)),
            ]:
                tk.Label(campos_frame, text=lbl + ":", bg=T.BG_CARD, fg=T.POS_TEXT, font=F_BODY).grid(
                    row=row, column=0, padx=(0, 10), pady=6, sticky="w"
                )
                e = tk.Entry(
                    campos_frame, width=30, font=F_BODY, bg=T.INPUT_BG, fg=T.POS_TEXT,
                    relief=tk.FLAT, highlightthickness=1, highlightbackground=T.INPUT_BORDER
                )
                e.insert(0, v0)
                e.grid(row=row, column=1, padx=0, pady=6, sticky="ew")
                entries[key] = e
                row += 1

        def guardar_cambios():
            if es_srv:
                ref = entries["referencia"].get().strip()
                nom = entries["nombre"].get().strip()
                try:
                    pr = float(entries["precio"].get().replace(",", ".") or 0)
                except ValueError:
                    messagebox.showerror("Datos", "Precio no válido.", parent=ventana_edicion)
                    return
                if actualizar_producto(
                    id_producto,
                    nom,
                    pr,
                    0,
                    0,
                    TIPO_SERVICIO,
                    referencia=ref,
                    categoria="",
                    parent_win=ventana_edicion,
                ):
                    messagebox.showinfo("Actualizado", "Cambios guardados correctamente.", parent=ventana_edicion)
                    ventana_edicion.destroy()
                    cargar_tabla()
            else:
                nom = entries["nombre"].get().strip()
                if not nom:
                    messagebox.showwarning("Datos", "El nombre es obligatorio.", parent=ventana_edicion)
                    return
                try:
                    pc = float(entries["p_compra"].get().replace(",", ".") or 0)
                    pv = float(entries["p_venta"].get().replace(",", ".") or 0)
                    st = int(entries["stock"].get().strip() or 0)
                except ValueError:
                    messagebox.showerror("Datos", "Valores numéricos no válidos.", parent=ventana_edicion)
                    return
                if actualizar_producto(
                    id_producto,
                    nom,
                    pv,
                    pc,
                    st,
                    TIPO_PRODUCTO,
                    referencia=None,
                    categoria=entries["categoria"].get().strip(),
                    parent_win=ventana_edicion,
                ):
                    messagebox.showinfo("Actualizado", "Cambios guardados correctamente.", parent=ventana_edicion)
                    ventana_edicion.destroy()
                    cargar_tabla()

        acciones = tk.Frame(card, bg=T.BG_CARD)
        acciones.pack(fill=tk.X, padx=20, pady=(8, 20))
        fbtn = tk.Frame(acciones, bg=T.BG_CARD)
        fbtn.pack(fill=tk.X)
        b_s = tk.Button(
            fbtn, text="Guardar cambios", font=F_BTN, bg=T.ACCENT, fg=T.WHITE, bd=0, pady=10,
            relief=tk.FLAT, cursor="hand2", command=guardar_cambios,
            activebackground=T.ACCENT_HOVER, activeforeground=T.WHITE
        )
        b_s.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        _btn_hover(b_s, T.ACCENT, T.ACCENT_HOVER)
        b_x = tk.Button(
            fbtn, text="Cancelar", font=F_BODY_B, bg=T.POS_BTN_ALT, fg=T.WHITE, bd=0, pady=10,
            relief=tk.FLAT, cursor="hand2", command=ventana_edicion.destroy, activebackground="#334155", activeforeground=T.WHITE
        )
        b_x.pack(side=tk.LEFT, fill=tk.X, expand=True)
        _btn_hover(b_x, T.POS_BTN_ALT, "#334155")
        if es_srv:
            entries["nombre"].focus()
        else:
            entries["nombre"].focus()

    def eliminar_producto_seleccionado():
        seleccionado = tabla.focus()
        if not seleccionado:
            messagebox.showwarning("Aviso", "Selecciona un producto para eliminar.")
            return

        valores = tabla.item(seleccionado)["values"]
        id_producto = valores[0]
        nombre_producto = valores[3]

        confirmacion = messagebox.askyesno("Confirmar Eliminación", 
                                         f"¿Estás seguro de que quieres eliminar '{nombre_producto}'?", 
                                         icon="warning")
        if confirmacion:
            if eliminar_producto(id_producto):
                messagebox.showinfo("Eliminado", "Producto eliminado correctamente.")
                cargar_tabla()

    def abrir_ganancias_productos():
        """Módulo: ganancias por producto y total real del día."""
        w = tk.Toplevel(ventana)
        w.title("Ganancias por productos")
        w.configure(bg=T.BG_APP)
        w.transient(ventana)
        w.grab_set()
        centrar_ventana(w, 980, 620, ventana)

        card = tk.Frame(w, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)

        tk.Label(card, text="Ganancias por productos", font=F_HEAD, bg=T.BG_CARD, fg=T.POS_TEXT).pack(
            anchor="w", padx=14, pady=(12, 4)
        )
        tk.Label(
            card,
            text="Ventas del día (contado y pagos efectivos) con utilidad por producto.",
            font=F_SMALL,
            bg=T.BG_CARD,
            fg=T.TEXT_MUTED,
        ).pack(anchor="w", padx=14, pady=(0, 10))

        top = tk.Frame(card, bg=T.BG_CARD)
        top.pack(fill=tk.X, padx=14, pady=(0, 8))
        tk.Label(top, text="Mes", font=F_BODY, bg=T.BG_CARD, fg=T.TEXT_MUTED).pack(side=tk.LEFT, padx=(0, 8))
        var_mes = tk.StringVar(value="")
        cb_mes = ttk.Combobox(top, textvariable=var_mes, state="readonly", width=10, font=F_BODY)
        cb_mes.pack(side=tk.LEFT, padx=(0, 12))
        tk.Label(top, text="Día", font=F_BODY, bg=T.BG_CARD, fg=T.TEXT_MUTED).pack(side=tk.LEFT, padx=(0, 8))
        var_dia = tk.StringVar(value="")
        cb_dia = ttk.Combobox(top, textvariable=var_dia, state="readonly", width=12, font=F_BODY)
        cb_dia.pack(side=tk.LEFT)
        lbl_resumen = tk.Label(top, text="", font=F_SMALL, bg=T.BG_CARD, fg=T.TEXT_MUTED)
        lbl_resumen.pack(side=tk.RIGHT)

        wrap = tk.Frame(card, bg=T.BG_SUBTLE, highlightbackground=T.BORDER, highlightthickness=1)
        wrap.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 8))
        cols = ("Código", "Producto", "Cantidad", "Vlr venta", "Vlr compra", "Ganancia/U", "Ganancia total")
        tv = ttk.Treeview(wrap, columns=cols, show="headings", height=18)
        tv.heading("Código", text="Código")
        tv.heading("Producto", text="Producto")
        tv.heading("Cantidad", text="Cantidad")
        tv.heading("Vlr venta", text="Vlr venta")
        tv.heading("Vlr compra", text="Vlr compra")
        tv.heading("Ganancia/U", text="Ganancia/U")
        tv.heading("Ganancia total", text="Ganancia total")
        tv.column("Código", width=90, anchor="center")
        tv.column("Producto", width=250, anchor="w")
        tv.column("Cantidad", width=90, anchor="center")
        tv.column("Vlr venta", width=120, anchor="e")
        tv.column("Vlr compra", width=120, anchor="e")
        tv.column("Ganancia/U", width=120, anchor="e")
        tv.column("Ganancia total", width=130, anchor="e")
        sy = ttk.Scrollbar(wrap, orient=tk.VERTICAL, command=tv.yview)
        tv.configure(yscrollcommand=sy.set)
        tv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(1, 0), pady=1)
        sy.pack(side=tk.RIGHT, fill=tk.Y, pady=1, padx=(0, 1))

        bottom = tk.Frame(card, bg=T.BG_CARD)
        bottom.pack(fill=tk.X, padx=14, pady=(0, 12))
        lbl_total_dia = tk.Label(
            bottom,
            text="Ganancia real del día: $0 COP",
            font=F_BODY_B,
            bg=T.BG_CARD,
            fg=T.POS_TEXT,
        )
        lbl_total_dia.pack(side=tk.LEFT)

        def _pk_ventas_expr(c):
            """Compatibilidad: algunas BD usan id y otras id_venta."""
            c.execute("PRAGMA table_info(ventas)")
            cols = {r[1] for r in c.fetchall()}
            if "id" in cols:
                return "id", cols
            if "id_venta" in cols:
                return "id_venta", cols
            return "rowid", cols

        def _normalizar_fecha_iso(fecha_txt):
            s = str(fecha_txt or "").strip()
            if not s:
                return None
            for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y"):
                try:
                    return datetime.strptime(s[:10], fmt).strftime("%Y-%m-%d")
                except Exception:
                    pass
            return None

        def _fechas_disponibles():
            conn = conectar_db()
            if not conn:
                return {}
            c = conn.cursor()
            fechas_por_dia = {}
            try:
                pk_col, _ = _pk_ventas_expr(c)
                c.execute(
                    f"""
                    SELECT DISTINCT v.fecha_venta
                    FROM ventas v
                    INNER JOIN detalle_ventas dv ON dv.id_venta = v.{pk_col}
                    WHERE TRIM(COALESCE(v.fecha_venta,'')) != ''
                    ORDER BY v.fecha_venta DESC
                    """
                )
                for r in c.fetchall():
                    if not r or not r[0]:
                        continue
                    raw = str(r[0]).strip()
                    iso = _normalizar_fecha_iso(raw)
                    if not iso:
                        continue
                    fechas_por_dia.setdefault(iso, set()).add(raw)
            except Exception:
                fechas_por_dia = {}
            conn.close()
            return fechas_por_dia

        def _cargar_ganancias():
            fecha_iso = (var_dia.get() or "").strip()
            for it in tv.get_children():
                tv.delete(it)
            if not fecha_iso:
                lbl_resumen.config(text="Sin día seleccionado")
                lbl_total_dia.config(text="Ganancia real del día: $0 COP")
                return
            conn = conectar_db()
            if not conn:
                return
            c = conn.cursor()
            total_dia = 0.0
            rows = []
            try:
                pk_col, cols_ventas = _pk_ventas_expr(c)
                filtro_tipo_pago = ""
                if "tipo_pago" in cols_ventas:
                    filtro_tipo_pago = " AND LOWER(COALESCE(v.tipo_pago, 'contado')) != 'fiado' "
                raw_vals = sorted(fechas_por_dia.get(fecha_iso, []))
                where_fecha = "DATE(v.fecha_venta) = ?"
                args = [fecha_iso]
                if raw_vals:
                    ph = ",".join(["?"] * len(raw_vals))
                    where_fecha = f"({where_fecha} OR v.fecha_venta IN ({ph}))"
                    args.extend(raw_vals)
                c.execute(
                    f"""
                    SELECT
                        COALESCE(dv.codigo_producto, 'N/A') AS codigo,
                        COALESCE(dv.nombre_producto, '(Sin nombre)') AS nombre,
                        SUM(COALESCE(dv.cantidad, 0)) AS qty,
                        AVG(COALESCE(dv.precio_unitario, 0)) AS p_venta_prom,
                        COALESCE(MAX(p.costo), 0) AS p_compra_ref,
                        SUM(COALESCE(dv.subtotal, 0)) AS subtotal
                    FROM detalle_ventas dv
                    INNER JOIN ventas v ON v.{pk_col} = dv.id_venta
                    LEFT JOIN productos p ON p.codigo = dv.codigo_producto
                    WHERE {where_fecha}
                      {filtro_tipo_pago}
                    GROUP BY dv.codigo_producto, dv.nombre_producto
                    ORDER BY subtotal DESC
                    """,
                    tuple(args),
                )
                rows = c.fetchall()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo calcular ganancias:\n{e}", parent=w)
            finally:
                conn.close()

            for cod, nom, qty, pventa, pcompra, subtotal in rows:
                q = float(qty or 0)
                pv = float(pventa or 0)
                pc = float(pcompra or 0)
                gan_u = pv - pc
                gan_t = float(subtotal or 0) - (q * pc)
                total_dia += gan_t
                tv.insert(
                    "",
                    "end",
                    values=(
                        str(cod),
                        str(nom),
                        int(q),
                        formato_peso(pv),
                        formato_peso(pc),
                        formato_peso(gan_u),
                        formato_peso(gan_t),
                    ),
                )
            lbl_resumen.config(text=f"Productos vendidos: {len(rows)}")
            lbl_total_dia.config(text=f"Ganancia real del día: {formato_peso(total_dia)}")

        def _dias_por_mes(mes_iso):
            dias = [d for d in fechas_por_dia.keys() if d.startswith(f"{mes_iso}-")]
            dias.sort(reverse=True)
            return dias

        def _on_cambio_mes(_e=None):
            mes = (var_mes.get() or "").strip()
            dias = _dias_por_mes(mes)
            cb_dia["values"] = dias
            if dias:
                var_dia.set(dias[0])
            else:
                var_dia.set("")
            _cargar_ganancias()

        fechas_por_dia = _fechas_disponibles()
        if fechas_por_dia:
            meses = sorted({d[:7] for d in fechas_por_dia.keys()}, reverse=True)
            cb_mes["values"] = meses
            var_mes.set(meses[0])
            _on_cambio_mes()
        else:
            hoy_iso = datetime.now().strftime("%Y-%m-%d")
            cb_mes["values"] = [hoy_iso[:7]]
            var_mes.set(hoy_iso[:7])
            cb_dia["values"] = [hoy_iso]
            var_dia.set(hoy_iso)
            fechas_por_dia = {hoy_iso: {hoy_iso}}
        _cargar_ganancias()
        cb_mes.bind("<<ComboboxSelected>>", _on_cambio_mes)
        cb_dia.bind("<<ComboboxSelected>>", lambda _e: _cargar_ganancias())

    # Barra lateral + panel principal (tarjetas estilo dashboard)
    panel_acciones = tk.Frame(
        main_content, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1
    )

    tk.Label(panel_acciones, text="Acciones", font=F_HEAD, bg=T.BG_CARD, fg=T.POS_TEXT).pack(
        pady=(16, 8), padx=16, anchor="w"
    )
    tk.Label(
        panel_acciones,
        text="Altas, edición y borrado del catálogo.",
        font=F_SMALL,
        bg=T.BG_CARD,
        fg=T.TEXT_MUTED,
        wraplength=190,
        justify=tk.LEFT,
    ).pack(padx=16, pady=(0, 12), anchor="w")

    f_btn_col = tk.Frame(panel_acciones, bg=T.BG_CARD)
    f_btn_col.pack(fill=tk.X, padx=12, pady=(0, 16))

    btn_barra_lateral(f_btn_col, "Nuevo ítem", T.ACCENT, T.ACCENT_HOVER, abrir_ventana_registro)
    btn_barra_lateral(f_btn_col, "Editar selección", T.STAT_1, "#0284c7", editar_producto)
    btn_barra_lateral(f_btn_col, "Eliminar", T.DANGER, "#b91c1c", eliminar_producto_seleccionado)
    btn_barra_lateral(f_btn_col, "Ganancias por productos", T.STAT_4, "#d97706", abrir_ganancias_productos)
    btn_accion_secundario(f_btn_col, "Actualizar lista", cargar_tabla)

    frame_tabla = tk.Frame(main_content, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)

    bind_reflow_pack(
        main_content,
        [
            (
                panel_acciones,
                {"side": tk.LEFT, "fill": tk.Y, "padx": (0, 12)},
                {"fill": tk.X, "pady": (0, 10)},
            ),
            (
                frame_tabla,
                {"side": tk.RIGHT, "fill": tk.BOTH, "expand": True},
                {"fill": tk.BOTH, "expand": True},
            ),
        ],
        umbral=860,
        debounce_ms=80,
    )

    hdr = tk.Frame(frame_tabla, bg=T.BG_CARD)
    hdr.pack(fill=tk.X, padx=16, pady=(14, 6))
    tk.Label(hdr, text="Catálogo", font=F_HEAD, bg=T.BG_CARD, fg=T.POS_TEXT).pack(side=tk.LEFT, anchor="w")
    tk.Label(
        hdr, textvariable=var_stats, font=F_SMALL, bg=T.BG_CARD, fg=T.TEXT_MUTED
    ).pack(side=tk.RIGHT, anchor="e")

    fila_bus = tk.Frame(frame_tabla, bg=T.BG_CARD)
    fila_bus.pack(fill=tk.X, padx=16, pady=(0, 6))
    tk.Label(fila_bus, text="Buscar", font=F_BODY, bg=T.BG_CARD, fg=T.TEXT_MUTED).pack(side=tk.LEFT, padx=(0, 8))
    ent_bus = tk.Entry(
        fila_bus, textvariable=var_busca, width=36, font=F_BODY, bg=T.INPUT_BG, fg=T.POS_TEXT,
        relief=tk.FLAT, highlightthickness=1, highlightbackground=T.INPUT_BORDER
    )
    ent_bus.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 12))
    ent_bus.bind("<KeyRelease>", lambda _e: cargar_tabla())
    lbl_scan_info = tk.Label(fila_bus, text="", font=F_SMALL, bg=T.BG_CARD, fg=T.TEXT_MUTED)
    lbl_scan_info.pack(side=tk.LEFT)

    fila_f = tk.Frame(frame_tabla, bg=T.BG_CARD)
    fila_f.pack(fill=tk.X, padx=16, pady=(0, 8))
    tk.Label(fila_f, text="Categoría", font=F_BODY, bg=T.BG_CARD, fg=T.TEXT_MUTED).pack(side=tk.LEFT, padx=(0, 8))
    cb_filtro = ttk.Combobox(
        fila_f, textvariable=var_filtro_tipo, state="readonly", width=22,
        values=("Todos", "Solo productos", "Solo servicios"), font=F_BODY,
    )
    cb_filtro.pack(side=tk.LEFT)
    cb_filtro.bind("<<ComboboxSelected>>", lambda _e: cargar_tabla())

    col_wrap = tk.Frame(frame_tabla, bg=T.BG_SUBTLE, highlightbackground=T.BORDER, highlightthickness=1)
    col_wrap.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))

    columnas = ("Id", "Código", "Referencia", "Nombre", "Categoría", "Tipo", "P. venta", "P. compra", "Stock")
    tabla = ttk.Treeview(col_wrap, columns=columnas, show="headings", height=16)

    style = ttk.Style(ventana)
    style_ttk_treeview_pos(style, T.BG_SUBTLE)

    tabla.heading("Id", text="Id")
    tabla.heading("Código", text="Código")
    tabla.heading("Referencia", text="Ref.")
    tabla.heading("Nombre", text="Nombre")
    tabla.heading("Categoría", text="Categoría")
    tabla.heading("Tipo", text="Tipo")
    tabla.heading("P. venta", text="P. venta")
    tabla.heading("P. compra", text="P. compra")
    tabla.heading("Stock", text="Stock")

    tabla.column("Id", width=36, anchor="center", minwidth=32)
    tabla.column("Código", width=72, anchor="center")
    tabla.column("Referencia", width=100, anchor="w")
    tabla.column("Nombre", width=160, anchor="w")
    tabla.column("Categoría", width=110, anchor="w")
    tabla.column("Tipo", width=80, anchor="center")
    tabla.column("P. venta", width=100, anchor="e")
    tabla.column("P. compra", width=100, anchor="e")
    tabla.column("Stock", width=56, anchor="center")

    scroll_y = ttk.Scrollbar(col_wrap, orient=tk.VERTICAL, command=tabla.yview)
    tabla.configure(yscrollcommand=scroll_y.set)
    tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(1, 0), pady=1)
    scroll_y.pack(side=tk.RIGHT, fill=tk.Y, pady=1, padx=(0, 1))
    
    # Cargar datos iniciales
    cargar_tabla()

    # Escaneo global en inventario: al timbrar Enter selecciona producto y muestra precio.
    scan_state = {"buf": "", "last_ts": 0.0}

    def _seleccionar_por_codigo(clave):
        c = (clave or "").strip().lower()
        if not c:
            return
        # Filtrar primero para dejar visible el resultado.
        var_busca.set(clave.strip())
        cargar_tabla()
        for iid in tabla.get_children():
            vals = tabla.item(iid).get("values", [])
            if len(vals) < 7:
                continue
            cod = str(vals[1]).strip().lower()
            ref = str(vals[2]).strip().lower()
            if c == cod or c == cod.zfill(5) or (ref and c == ref):
                tabla.selection_set(iid)
                tabla.focus(iid)
                tabla.see(iid)
                nombre = str(vals[3]).strip()
                precio = str(vals[6]).strip()
                lbl_scan_info.config(text=f"Escaneado: {nombre} · Precio: {precio}", fg=T.SUCCESS)
                return
        lbl_scan_info.config(text="Código no encontrado en inventario", fg=T.DANGER)

    def _capturar_scanner_global(event):
        try:
            import time
            now = time.time()
            if event.keysym == "Return":
                buf = (scan_state["buf"] or "").strip()
                scan_state["buf"] = ""
                scan_state["last_ts"] = now
                if len(buf) >= 3:
                    _seleccionar_por_codigo(buf)
                    return "break"
                return None
            ch = event.char or ""
            if len(ch) == 1 and ch.isprintable():
                if now - float(scan_state["last_ts"] or 0) > 0.18:
                    scan_state["buf"] = ""
                scan_state["buf"] += ch
                scan_state["last_ts"] = now
        except Exception:
            return None
        return None

    # Solo escuchar teclado dentro de esta ventana (evita eventos cuando el módulo ya se cerró).
    ventana.bind("<KeyPress>", _capturar_scanner_global, add="+")

    modulo_scroll_finalizar(cuerpo)

    if parent is None:
        ventana.mainloop()

if __name__ == "__main__":
    iniciar_inventario()