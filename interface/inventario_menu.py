# --- Proposed Changes for inventario_menu.py ---

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import sqlite3
import os

# 📦 Ruta de la base de datos (Keep as is)
ruta_db = os.path.join(os.path.dirname(__file__), '..', 'database', 'ventas.db')

# 💵 Formato de pesos colombianos (Keep as is)
def formato_peso(valor):
    if valor is None:
        return "$0 COP"
    return f"${valor:,.0f} COP"

# 🧩 Funciones de base de datos (Keep as is)
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
    cursor.execute("SELECT id, nombre, precio, costo, stock FROM productos")
    productos = cursor.fetchall()
    conn.close()
    return productos

# 🖥️ Interfaz principal
def iniciar_inventario():
    ventana = tk.Tk()
    ventana.title("Inventario - VmPOS")
    ventana.geometry("980x540")
    ventana.resizable(False, False) # Added for consistency
    ventana.configure(bg="#ff9ff3") # Main window background

    # Centrar ventana (Copied from menu_inicio.py)
    ventana.update_idletasks()
    x = (ventana.winfo_screenwidth() // 2) - (980 // 2) # Adjust width for inventory window
    y = (ventana.winfo_screenheight() // 2) - (540 // 2) # Adjust height for inventory window
    ventana.geometry(f"980x540+{x}+{y}")

    # 🎨 Header principal (Adapted from menu_inicio.py)
    header_frame = tk.Frame(ventana, bg="#e84393", height=80)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)

    header_left = tk.Frame(header_frame, bg="#e84393")
    header_left.pack(side="left", fill="y", padx=30)

    tk.Label(header_left, text="🎀", font=("Segoe UI Emoji", 28),
             bg="#e84393", fg="white").pack(side="left", pady=15) # Changed icon
    tk.Label(header_left, text="INVENTARIO", font=("Segoe UI", 24, "bold"),
             bg="#e84393", fg="white").pack(side="left", padx=(10, 0), pady=18)
    tk.Label(header_left, text="Gestión de Productos", font=("Segoe UI", 12),
             bg="#e84393", fg="#ffd3e8").pack(side="left", padx=(15, 0), pady=20)


    # Info fecha y hora en header_right (Adapted from menu_inicio.py)
    header_right = tk.Frame(header_frame, bg="#e84393")
    header_right.pack(side="right", fill="y", padx=30)

    lbl_fecha = tk.Label(header_right, text="", font=("Segoe UI", 10), bg="#e84393", fg="#ffd3e8")
    lbl_fecha.pack(anchor="e", pady=(12, 2))

    lbl_hora = tk.Label(header_right, text="", font=("Segoe UI", 10), bg="#e84393", fg="#ffd3e8")
    lbl_hora.pack(anchor="e")

    def actualizar_tiempo():
        ahora = datetime.now()
        lbl_fecha.config(text=f"📅 {ahora.strftime('%d/%m/%Y')}") # Consistent date format
        lbl_hora.config(text=f"🕐 {ahora.strftime('%H:%M:%S')}") # Consistent time format
        ventana.after(1000, actualizar_tiempo)

    actualizar_tiempo()

    # 📊 Main Content Area (Similar to main_content in menu_inicio.py)
    main_content = tk.Frame(ventana, bg="#ffeaa7")
    main_content.pack(fill="both", expand=True, padx=20, pady=20)


    def cargar_tabla():
        for item in tabla.get_children():
            tabla.delete(item)
        for producto in obtener_productos():
            id, nombre, precio, costo, stock = producto
            tabla.insert("", "end", values=(
                id, nombre, formato_peso(precio), formato_peso(costo), stock
            ))

    # Helper function for modern buttons (Copied and adapted from menu_inicio.py)
    def crear_boton_moderno(parent, texto, icono, color, comando):
        btn_frame = tk.Frame(parent, bg="#ffeaa7") # Parent background
        btn_frame.pack(fill="x", padx=10, pady=5) # Reduced padx/pady for inventory context

        btn = tk.Button(btn_frame, text=f"{icono}  {texto}",
                        font=("Segoe UI", 12, "bold"), bg=color, fg="white",
                        bd=0, pady=10, cursor="hand2", command=comando,
                        relief="flat", anchor="w", padx=15) # Adjusted padding
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
        ventana_registro = tk.Toplevel(ventana) # Link to parent window
        ventana_registro.title("Registrar nuevo producto")
        ventana_registro.geometry("380x380") # Increased height
        ventana_registro.configure(bg="#FFF0F5")
        ventana_registro.transient(ventana) # Make it a modal window
        ventana_registro.grab_set() # Grab focus

        # Center new window relative to parent (simple version)
        ventana_registro.update_idletasks()
        x_offset = ventana.winfo_x() + (ventana.winfo_width() // 2) - (380 // 2)
        y_offset = ventana.winfo_y() + (ventana.winfo_height() // 2) - (380 // 2)
        ventana_registro.geometry(f"380x380+{x_offset}+{y_offset}")

        tk.Label(ventana_registro, text="Nuevo Producto", font=("Segoe UI", 14, "bold"), bg="#FFF0F5", fg="#e84393").pack(pady=10)

        campos_frame = tk.Frame(ventana_registro, bg="#FFF0F5")
        campos_frame.pack(pady=10)

        campos = {
            "Código": tk.StringVar(),
            "Nombre": tk.StringVar(),
            "Precio": tk.DoubleVar(),
            "Costo": tk.DoubleVar(),
            "Stock": tk.IntVar()
        }

        row = 0
        for campo, var in campos.items():
            tk.Label(campos_frame, text=campo + ":", bg="#FFF0F5", font=("Segoe UI", 10)).grid(row=row, column=0, padx=10, pady=5, sticky="w")
            tk.Entry(campos_frame, textvariable=var, width=35, font=("Segoe UI", 10), bd=1, relief="solid").grid(row=row, column=1, padx=10, pady=5)
            row += 1

        def registrar():
            try:
                guardar_producto(
                    campos["Código"].get(),
                    campos["Nombre"].get(),
                    campos["Precio"].get(),
                    campos["Costo"].get(),
                    campos["Stock"].get()
                )
                messagebox.showinfo("Éxito", "Producto registrado exitosamente.", parent=ventana_registro) # Parent for message box
                ventana_registro.destroy()
                cargar_tabla()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo registrar el producto: {e}", parent=ventana_registro)

        # Use modern button for "Guardar"
        crear_boton_moderno(ventana_registro, "Guardar Producto", "✅", "#55efc4", registrar).pack(pady=15, padx=20)
        ventana_registro.wait_window() # Wait for this window to close

    def editar_producto():
        seleccionado = tabla.focus()
        if not seleccionado:
            messagebox.showwarning("Aviso", "Selecciona un producto para editar.")
            return

        valores = tabla.item(seleccionado)["values"]
        id_producto = valores[0]

        precio = float(valores[2].replace("$", "").replace("COP", "").replace(",", "").strip())
        costo = float(valores[3].replace("$", "").replace("COP", "").replace(",", "").strip())
        stock = valores[4]
        nombre = valores[1]

        ventana_edicion = tk.Toplevel(ventana) # Link to parent window
        ventana_edicion.title("Editar producto")
        ventana_edicion.geometry("380x380") # Increased height
        ventana_edicion.configure(bg="#FFF0F5")
        ventana_edicion.transient(ventana) # Make it a modal window
        ventana_edicion.grab_set() # Grab focus

        # Center new window relative to parent (simple version)
        ventana_edicion.update_idletasks()
        x_offset = ventana.winfo_x() + (ventana.winfo_width() // 2) - (380 // 2)
        y_offset = ventana.winfo_y() + (ventana.winfo_height() // 2) - (380 // 2)
        ventana_edicion.geometry(f"380x380+{x_offset}+{y_offset}")

        tk.Label(ventana_edicion, text="Editar Producto", font=("Segoe UI", 14, "bold"), bg="#FFF0F5", fg="#e84393").pack(pady=10)

        campos_frame = tk.Frame(ventana_edicion, bg="#FFF0F5")
        campos_frame.pack(pady=10)

        campos = {
            "Nombre": tk.StringVar(value=nombre),
            "Precio": tk.DoubleVar(value=precio),
            "Costo": tk.DoubleVar(value=costo),
            "Stock": tk.IntVar(value=stock)
        }

        row = 0
        for campo, var in campos.items():
            tk.Label(campos_frame, text=campo + ":", bg="#FFF0F5", font=("Segoe UI", 10)).grid(row=row, column=0, padx=10, pady=5, sticky="w")
            tk.Entry(campos_frame, textvariable=var, width=35, font=("Segoe UI", 10), bd=1, relief="solid").grid(row=row, column=1, padx=10, pady=5)
            row += 1

        def guardar_cambios():
            try:
                actualizar_producto(
                    id_producto,
                    campos["Nombre"].get(),
                    campos["Precio"].get(),
                    campos["Costo"].get(),
                    campos["Stock"].get()
                )
                messagebox.showinfo("Actualizado", "Producto editado correctamente.", parent=ventana_edicion)
                ventana_edicion.destroy()
                cargar_tabla()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo editar el producto: {e}", parent=ventana_edicion)

        # Use modern button for "Guardar cambios"
        crear_boton_moderno(ventana_edicion, "Guardar Cambios", "💾", "#74b9ff", guardar_cambios).pack(pady=15, padx=20)
        ventana_edicion.wait_window()

    def eliminar_producto_seleccionado():
        seleccionado = tabla.focus()
        if not seleccionado:
            messagebox.showwarning("Aviso", "Selecciona un producto para eliminar.")
            return

        valores = tabla.item(seleccionado)["values"]
        id_producto = valores[0]
        nombre_producto = valores[1] # Get product name for confirmation

        confirmacion = messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de que quieres eliminar '{nombre_producto}'?", icon="warning")
        if confirmacion:
            try:
                eliminar_producto(id_producto)
                messagebox.showinfo("Eliminado", "Producto eliminado correctamente.")
                cargar_tabla()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar el producto: {e}")

    # Panel for main action buttons (within main_content and with white background)
    panel_acciones = tk.Frame(main_content, bg="white", bd=3, relief="solid")
    panel_acciones.pack(side="left", fill="y", padx=(0, 10), pady=0) # Aligned left

    tk.Label(panel_acciones, text="⚙️ ACCIONES", font=("Segoe UI", 14, "bold"),
             bg="white", fg="#e84393").pack(pady=20, padx=10) # Added padx

    # Use modern buttons for actions
    crear_boton_moderno(panel_acciones, "Registrar", "➕", "#fd79a8", abrir_ventana_registro)
    crear_boton_moderno(panel_acciones, "Editar", "✏️", "#74b9ff", editar_producto)
    crear_boton_moderno(panel_acciones, "Eliminar", "🗑️", "#ff7675", eliminar_producto_seleccionado)
    crear_boton_moderno(panel_acciones, "Exportar", "📤", "#fdcb6e", lambda: messagebox.showinfo("Info", "Funcionalidad de exportar no implementada aún."))


    frame_tabla = tk.Frame(main_content, bg="white", bd=3, relief="solid") # Changed background
    frame_tabla.pack(side="right", fill="both", expand=True, pady=0, padx=0)

    # Add a title above the table
    tk.Label(frame_tabla, text="📦 LISTADO DE PRODUCTOS", font=("Segoe UI", 14, "bold"),
             bg="white", fg="#e84393").pack(pady=20)


    columnas = ("Id", "Producto", "Precio", "Costo", "Stock")
    tabla = ttk.Treeview(frame_tabla, columns=columnas, show="headings", height=15) # Increased height
    
    # Configure Treeview style to match the modern look (requires a theme)
    style = ttk.Style()
    style.theme_use('clam') # 'clam' or 'alt' themes offer more customization
    style.configure("Treeview",
                    background="white",
                    foreground="#2d3436",
                    rowheight=25,
                    fieldbackground="white",
                    font=("Segoe UI", 10))
    style.map("Treeview",
              background=[('selected', '#fd79a8')], # Selection color
              foreground=[('selected', 'white')])

    style.configure("Treeview.Heading",
                    font=("Segoe UI", 10, "bold"),
                    background="#e84393", # Header background
                    foreground="white",    # Header text color
                    relief="flat")
    style.map("Treeview.Heading",
              background=[('active', '#e84393')]) # Active header background


    for col in columnas:
        tabla.heading(col, text=col)
        tabla.column(col, width=130, anchor="center")
    tabla.pack(fill="both", expand=True, padx=20, pady=10) # Added expand, padx/pady
    cargar_tabla()

    # 📊 Footer con información del sistema (Copied from menu_inicio.py)
    footer = tk.Frame(ventana, bg="#e84393", height=50)
    footer.pack(fill="x")
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