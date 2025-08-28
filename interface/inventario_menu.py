import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import sqlite3
import os

# 📦 Ruta de la base de datos
base_dir = os.path.dirname(os.path.abspath(__file__))
ruta_db = os.path.join(base_dir, '..', 'database', 'ventas.db')

# 💵 Formato de pesos colombianos
def formato_peso(valor):
    if valor is None or valor == '':
        return "$0 COP"
    return f"${valor:,.0f} COP"

def limpiar_precio(texto):
    """Limpia una cadena de texto para extraer un valor numérico flotante."""
    texto = texto.replace("$", "").replace("COP", "").replace(",", "").strip()
    try:
        # Aquí se asume que las comas son separadores de miles
        return float(texto.replace(",", ""))
    except ValueError:
        return 0.0

# 🧩 Funciones de base de datos
def guardar_producto(codigo, nombre, precio, costo, stock):
    conn = sqlite3.connect(ruta_db)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO productos (codigo, nombre, precio, costo, stock)
        VALUES (?, ?, ?, ?, ?)
    """, (codigo, nombre, precio, costo, stock))
    conn.commit()
    conn.close()

def actualizar_producto(id_producto, nombre, precio, costo, stock):
    conn = sqlite3.connect(ruta_db)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE productos
        SET nombre = ?, precio = ?, costo = ?, stock = ?
        WHERE id = ?
    """, (nombre, precio, costo, stock, id_producto))
    conn.commit()
    conn.close()

def eliminar_producto(id_producto):
    conn = sqlite3.connect(ruta_db)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM productos WHERE id = ?", (id_producto,))
    conn.commit()
    conn.close()

def obtener_productos():
    conn = sqlite3.connect(ruta_db)
    cursor = conn.cursor()
    cursor.execute("SELECT id, codigo, nombre, precio, costo, stock FROM productos")
    productos = cursor.fetchall()
    conn.close()
    return productos

# 🖥️ Interfaz principal
def iniciar_inventario():
    ventana = tk.Tk()
    ventana.title("Inventario - VmPOS")
    ventana.geometry("980x540")
    ventana.resizable(False, False)
    ventana.configure(bg="#ff9ff3")

    # Centrar ventana
    ventana.update_idletasks()
    x = (ventana.winfo_screenwidth() // 2) - (980 // 2)
    y = (ventana.winfo_screenheight() // 2) - (540 // 2)
    ventana.geometry(f"980x540+{x}+{y}")

    # 🎨 Header principal
    header_frame = tk.Frame(ventana, bg="#e84393", height=80)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)

    header_left = tk.Frame(header_frame, bg="#e84393")
    header_left.pack(side="left", fill="y", padx=30)

    tk.Label(header_left, text="🎀", font=("Segoe UI Emoji", 28),
             bg="#e84393", fg="white").pack(side="left", pady=15)
    tk.Label(header_left, text="INVENTARIO", font=("Segoe UI", 24, "bold"),
             bg="#e84393", fg="white").pack(side="left", padx=(10, 0), pady=18)
    tk.Label(header_left, text="Gestión de Productos", font=("Segoe UI", 12),
             bg="#e84393", fg="#ffd3e8").pack(side="left", padx=(15, 0), pady=20)


    # Info fecha y hora en header_right
    header_right = tk.Frame(header_frame, bg="#e84393")
    header_right.pack(side="right", fill="y", padx=30)

    lbl_fecha = tk.Label(header_right, text="", font=("Segoe UI", 10), bg="#e84393", fg="#ffd3e8")
    lbl_fecha.pack(anchor="e", pady=(12, 2))

    lbl_hora = tk.Label(header_right, text="", font=("Segoe UI", 10), bg="#e84393", fg="#ffd3e8")
    lbl_hora.pack(anchor="e")

    def actualizar_tiempo():
        ahora = datetime.now()
        lbl_fecha.config(text=f"📅 {ahora.strftime('%d/%m/%Y')}")
        lbl_hora.config(text=f"🕐 {ahora.strftime('%H:%M:%S')}")
        ventana.after(1000, actualizar_tiempo)

    actualizar_tiempo()

    # 📊 Main Content Area
    main_content = tk.Frame(ventana, bg="#ffeaa7")
    main_content.pack(fill="both", expand=True, padx=20, pady=20)


    def cargar_tabla():
        for item in tabla.get_children():
            tabla.delete(item)
        for producto in obtener_productos():
            id, codigo, nombre, precio, costo, stock = producto
            tabla.insert("", "end", values=(
                id, codigo, nombre, formato_peso(precio), formato_peso(costo), stock
            ))

    # Helper function for modern buttons
    def crear_boton_moderno(parent, texto, icono, color, comando):
        btn_frame = tk.Frame(parent, bg="#ffeaa7")
        btn_frame.pack(fill="x", padx=10, pady=5)

        btn = tk.Button(btn_frame, text=f"{icono}  {texto}",
                        font=("Segoe UI", 12, "bold"), bg=color, fg="white",
                        bd=0, pady=10, cursor="hand2", command=comando,
                        relief="flat", anchor="w", padx=15)
        btn.pack(fill="x")

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
            btn.config(bg=color)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

        return btn

    def abrir_ventana_registro():
        ventana_registro = tk.Toplevel(ventana)
        ventana_registro.title("Registrar nuevo producto")
        ventana_registro.geometry("380x380")
        ventana_registro.configure(bg="#FFF0F5")
        ventana_registro.transient(ventana)
        ventana_registro.grab_set()

        ventana_registro.update_idletasks()
        x_offset = ventana.winfo_x() + (ventana.winfo_width() // 2) - (380 // 2)
        y_offset = ventana.winfo_y() + (ventana.winfo_height() // 2) - (380 // 2)
        ventana_registro.geometry(f"380x380+{x_offset}+{y_offset}")

        tk.Label(ventana_registro, text="Nuevo Producto", font=("Segoe UI", 14, "bold"), bg="#FFF0F5", fg="#e84393").pack(pady=10)

        campos_frame = tk.Frame(ventana_registro, bg="#FFF0F5")
        campos_frame.pack(pady=10)
        
        entries = {}
        row = 0
        for campo in ["Código", "Nombre", "Precio", "Costo", "Stock"]:
            tk.Label(campos_frame, text=campo + ":", bg="#FFF0F5", font=("Segoe UI", 10)).grid(row=row, column=0, padx=10, pady=5, sticky="w")
            entry = tk.Entry(campos_frame, width=35, font=("Segoe UI", 10), bd=1, relief="solid")
            entry.grid(row=row, column=1, padx=10, pady=5)
            entries[campo] = entry
            row += 1

        def registrar():
            codigo = entries["Código"].get().strip()
            nombre = entries["Nombre"].get().strip()
            precio_str = entries["Precio"].get().strip()
            costo_str = entries["Costo"].get().strip()
            stock_str = entries["Stock"].get().strip()

            if not codigo or not nombre:
                messagebox.showwarning("Campos vacíos", "El código y el nombre del producto son obligatorios.", parent=ventana_registro)
                return

            try:
                precio = float(precio_str) if precio_str else 0.0
                costo = float(costo_str) if costo_str else 0.0
                stock = int(stock_str) if stock_str else 0
                
                # --- AQUÍ ESTÁ LA CORRECCIÓN CLAVE ---
                # Se asegura que el código siempre tenga 5 dígitos.
                codigo_formateado = codigo.zfill(5)
                
                guardar_producto(codigo_formateado, nombre, precio, costo, stock)
                messagebox.showinfo("Éxito", "Producto registrado exitosamente.", parent=ventana_registro)
                ventana_registro.destroy()
                cargar_tabla()
            except ValueError:
                messagebox.showerror("Error de formato", "Por favor, introduce valores numéricos válidos para Precio, Costo y Stock.", parent=ventana_registro)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo registrar el producto: {e}", parent=ventana_registro)

        crear_boton_moderno(ventana_registro, "Guardar Producto", "✅", "#55efc4", registrar).pack(pady=15, padx=20)
        ventana_registro.wait_window()

    def editar_producto():
        seleccionado = tabla.focus()
        if not seleccionado:
            messagebox.showwarning("Aviso", "Selecciona un producto para editar.")
            return

        valores = tabla.item(seleccionado)["values"]
        id_producto = valores[0]
        codigo = valores[1]
        nombre = valores[2]
        precio_val = limpiar_precio(valores[3])
        costo_val = limpiar_precio(valores[4])
        stock_val = valores[5]

        ventana_edicion = tk.Toplevel(ventana)
        ventana_edicion.title("Editar producto")
        ventana_edicion.geometry("380x380")
        ventana_edicion.configure(bg="#FFF0F5")
        ventana_edicion.transient(ventana)
        ventana_edicion.grab_set()

        ventana_edicion.update_idletasks()
        x_offset = ventana.winfo_x() + (ventana.winfo_width() // 2) - (380 // 2)
        y_offset = ventana.winfo_y() + (ventana.winfo_height() // 2) - (380 // 2)
        ventana_edicion.geometry(f"380x380+{x_offset}+{y_offset}")

        tk.Label(ventana_edicion, text="Editar Producto", font=("Segoe UI", 14, "bold"), bg="#FFF0F5", fg="#e84393").pack(pady=10)

        campos_frame = tk.Frame(ventana_edicion, bg="#FFF0F5")
        campos_frame.pack(pady=10)
        
        entries = {}
        row = 0
        campos = [
            ("Código", codigo), 
            ("Nombre", nombre), 
            ("Precio", str(precio_val)), 
            ("Costo", str(costo_val)), 
            ("Stock", str(stock_val))
        ]
        
        for campo, valor in campos:
            tk.Label(campos_frame, text=campo + ":", bg="#FFF0F5", font=("Segoe UI", 10)).grid(row=row, column=0, padx=10, pady=5, sticky="w")
            entry = tk.Entry(campos_frame, width=35, font=("Segoe UI", 10), bd=1, relief="solid")
            entry.insert(0, valor) # Pre-populate with existing value
            # El código no debe ser editable para evitar inconsistencias
            if campo == "Código":
                entry.config(state="readonly")
            entry.grid(row=row, column=1, padx=10, pady=5)
            entries[campo] = entry
            row += 1

        def guardar_cambios():
            nombre = entries["Nombre"].get().strip()
            precio_str = entries["Precio"].get().strip()
            costo_str = entries["Costo"].get().strip()
            stock_str = entries["Stock"].get().strip()

            if not nombre:
                messagebox.showwarning("Campo vacío", "El nombre del producto es obligatorio.", parent=ventana_edicion)
                return

            try:
                precio = float(precio_str) if precio_str else 0.0
                costo = float(costo_str) if costo_str else 0.0
                stock = int(stock_str) if stock_str else 0
                
                actualizar_producto(id_producto, nombre, precio, costo, stock)
                messagebox.showinfo("Actualizado", "Producto editado correctamente.", parent=ventana_edicion)
                ventana_edicion.destroy()
                cargar_tabla()
            except ValueError:
                messagebox.showerror("Error de formato", "Por favor, introduce valores numéricos válidos para Precio, Costo y Stock.", parent=ventana_edicion)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo editar el producto: {e}", parent=ventana_edicion)

        crear_boton_moderno(ventana_edicion, "Guardar Cambios", "💾", "#74b9ff", guardar_cambios).pack(pady=15, padx=20)
        ventana_edicion.wait_window()

    def eliminar_producto_seleccionado():
        seleccionado = tabla.focus()
        if not seleccionado:
            messagebox.showwarning("Aviso", "Selecciona un producto para eliminar.")
            return

        valores = tabla.item(seleccionado)["values"]
        id_producto = valores[0]
        nombre_producto = valores[2]

        confirmacion = messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de que quieres eliminar '{nombre_producto}'?", icon="warning")
        if confirmacion:
            try:
                eliminar_producto(id_producto)
                messagebox.showinfo("Eliminado", "Producto eliminado correctamente.")
                cargar_tabla()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar el producto: {e}")

    # Panel for main action buttons
    panel_acciones = tk.Frame(main_content, bg="white", bd=3, relief="solid")
    panel_acciones.pack(side="left", fill="y", padx=(0, 10), pady=0)

    tk.Label(panel_acciones, text="⚙️ ACCIONES", font=("Segoe UI", 14, "bold"),
             bg="white", fg="#e84393").pack(pady=20, padx=10)

    crear_boton_moderno(panel_acciones, "Registrar", "➕", "#fd79a8", abrir_ventana_registro)
    crear_boton_moderno(panel_acciones, "Editar", "✏️", "#74b9ff", editar_producto)
    crear_boton_moderno(panel_acciones, "Eliminar", "🗑️", "#ff7675", eliminar_producto_seleccionado)
    crear_boton_moderno(panel_acciones, "Exportar", "📤", "#fdcb6e", lambda: messagebox.showinfo("Info", "Funcionalidad de exportar no implementada aún."))


    frame_tabla = tk.Frame(main_content, bg="white", bd=3, relief="solid")
    frame_tabla.pack(side="right", fill="both", expand=True, pady=0, padx=0)

    tk.Label(frame_tabla, text="📦 LISTADO DE PRODUCTOS", font=("Segoe UI", 14, "bold"),
             bg="white", fg="#e84393").pack(pady=20)


    columnas = ("Id", "Código", "Producto", "Precio", "Costo", "Stock")
    tabla = ttk.Treeview(frame_tabla, columns=columnas, show="headings", height=15)
    
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("Treeview",
                    background="white",
                    foreground="#2d3436",
                    rowheight=25,
                    fieldbackground="white",
                    font=("Segoe UI", 10))
    style.map("Treeview",
              background=[('selected', '#fd79a8')],
              foreground=[('selected', 'white')])

    style.configure("Treeview.Heading",
                    font=("Segoe UI", 10, "bold"),
                    background="#e84393",
                    foreground="white",
                    relief="flat")
    style.map("Treeview.Heading",
              background=[('active', '#e84393')])


    tabla.heading("Id", text="Id")
    tabla.heading("Código", text="Código")
    tabla.heading("Producto", text="Producto")
    tabla.heading("Precio", text="Precio")
    tabla.heading("Costo", text="Costo")
    tabla.heading("Stock", text="Stock")

    tabla.column("Id", width=40, anchor="center")
    tabla.column("Código", width=100, anchor="center")
    tabla.column("Producto", width=200, anchor="w")
    tabla.column("Precio", width=120, anchor="center")
    tabla.column("Costo", width=120, anchor="center")
    tabla.column("Stock", width=80, anchor="center")

    tabla.pack(fill="both", expand=True, padx=20, pady=10)
    cargar_tabla()

    # 📊 Footer con información del sistema
    footer = tk.Frame(ventana, bg="#e84393", height=50)
    footer.pack(fill="x", side="bottom")
    footer.pack_propagate(False)

    footer_left = tk.Frame(footer, bg="#e84393")
    footer_left.pack(side="left", padx=20, pady=10)

    footer_right = tk.Frame(footer, bg="#e84393")
    footer_right.pack(side="right", padx=20, pady=10)

    tk.Label(footer_left, text="📍 Puerto Colombia • 📞 +573215545788",
             font=("Segoe UI", 10), bg="#e84393", fg="white").pack()

    tk.Label(footer_right, text="✨ VmPOS v3.1.0 • Sistema Activo 💖",
             font=("Segoe UI", 10), bg="#e84393", fg="#ffd3e8").pack()

    ventana.mainloop()

if __name__ == "__main__":
    iniciar_inventario()