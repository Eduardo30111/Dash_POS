import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import os
from escpos.printer import Usb


base_dir = os.path.dirname(__file__)
ruta_db = os.path.join(base_dir, '..', 'database', 'ventas.db')

# 🔌 Conexión a la base de datos
def obtener_productos():
    try:
        conn = sqlite3.connect(ruta_db)
    except Exception as e:
        messagebox.showerror("Error de conexión", f"No se pudo abrir la base de datos:\n{e}")
        return []
    cursor = conn.cursor()
    cursor.execute("SELECT codigo, nombre, stock, precio FROM productos")
    productos = cursor.fetchall()
    conn.close()
    return productos

# 💵 Formato pesos colombianos
def formato_peso(valor):
    return f"${valor:,.0f} COP"

# 🔄 Limpiar texto de precios para convertir a float  
def limpiar_precio(texto):
    texto = texto.replace("$", "").replace("COP", "").replace(",", "").replace(".", "").strip()
    try:
        return float(texto)
    except:
        return 0.0

# 🖨️ Función para imprimir factura en impresora térmica 58mm
def imprimir_factura_termica(documento_cliente, usuario, productos, total_general, factura_num, fecha, hora):
    try:
        # Lista de IDs comunes para impresoras térmicas DigitalPOS/Genéricas
        ids_impresoras = [
            (0x0fe6, 0x811e),  # DigitalPOS común
            (0x04b8, 0x0202),  # Epson compatible
            (0x04b8, 0x0e15),  # Epson TM-T20
            (0x154f, 0x154f),  # Genérica
            (0x1fc9, 0x2016),  # Otra común
            (0x0483, 0x5743),  # STMicroelectronics
        ]
        
        p = None
        for vendor_id, product_id in ids_impresoras:
            try:
                p = Usb(vendor_id, product_id)
                break
            except:
                continue
        
        if p is None:
            raise Exception("No se encontró ninguna impresora compatible conectada")
        
        # Configurar para papel de 58mm - usando parámetros correctos
        p.set(align='center', bold=True, double_width=False, double_height=False)
        p.text("VARIEDADES MARCE\n")
        p.set(align='center', bold=False)
        p.text("Centro de copiado y belleza\n")
        p.text("Cel: 300-123-4567\n")
        p.text("=" * 32 + "\n")
        
        p.set(align='left', bold=False)
        p.text(f"Factura: {factura_num}\n")
        p.text(f"Fecha: {fecha}\n")
        p.text(f"Hora: {hora}\n")
        p.text(f"Cliente: {documento_cliente}\n")
        p.text(f"Vendedora: {usuario}\n")
        p.text("-" * 32 + "\n")
        
        # Encabezado de productos
        p.text("Producto      Cant  Precio\n")
        p.text("-" * 32 + "\n")

        total_items = 0
        for nombre, precio, cantidad in productos:
            subtotal = precio * cantidad
            total_items += cantidad
            # Ajustar formato para 58mm
            nombre_corto = nombre[:12] if len(nombre) > 12 else nombre
            p.text(f"{nombre_corto:<12} {cantidad:>2}x ${precio:>6,.0f}\n")
            p.text(f"              Subtotal: ${subtotal:>8,.0f}\n")

        p.text("-" * 32 + "\n")
        p.text(f"Total Items: {total_items}\n")
        p.set(bold=True)
        p.text(f"TOTAL: ${total_general:>16,.0f}\n")
        p.set(bold=False)
        p.text("=" * 32 + "\n")
        p.set(align='center')
        p.text("Gracias por tu compra!\n")
        p.text("Vuelve pronto\n")
        p.text("=" * 32 + "\n")
        p.text("\n\n")
        p.cut()
        
        messagebox.showinfo("✅ Impresión", "¡Factura impresa exitosamente! 💖")
        
    except Exception as e:
        # Crear ventana personalizada para el error con funcionalidad Enter
        ventana_error = tk.Toplevel()
        ventana_error.title("❌ Error de impresión")
        ventana_error.geometry("500x250")
        ventana_error.configure(bg="#FFB6C1")
        ventana_error.transient(ventana)
        ventana_error.grab_set()
        
        # Centrar la ventana de error
        ventana_error.update_idletasks()
        x = (ventana_error.winfo_screenwidth() // 2) - (250)
        y = (ventana_error.winfo_screenheight() // 2) - (125)
        ventana_error.geometry(f"500x250+{x}+{y}")
        
        tk.Label(ventana_error, text="❌ ERROR DE IMPRESIÓN", 
                font=("Arial", 14, "bold"), bg="#FFB6C1", fg="#8B0054").pack(pady=10)
        
        tk.Label(ventana_error, text="No se pudo conectar con la impresora:", 
                font=("Arial", 10), bg="#FFB6C1", fg="#8B0054").pack(pady=5)
        
        # Área de texto para mostrar el error
        error_text = tk.Text(ventana_error, height=4, width=50, wrap=tk.WORD)
        error_text.pack(pady=10, padx=20)
        error_text.insert("1.0", str(e))
        error_text.config(state=tk.DISABLED)
        
        tk.Label(ventana_error, text="💡 Soluciones:", 
                font=("Arial", 10, "bold"), bg="#FFB6C1", fg="#8B0054").pack(pady=5)
        
        soluciones = """• Verifica que la impresora esté conectada y encendida
• Instala el driver de la impresora DigitalPOS
• Revisa el cable USB
• Reinicia la impresora"""
        
        tk.Label(ventana_error, text=soluciones, 
                font=("Arial", 9), bg="#FFB6C1", fg="#8B0054", justify="left").pack(pady=5)
        
        def cerrar_error():
            ventana_error.destroy()
        
        btn_aceptar = tk.Button(ventana_error, text="✅ Aceptar", 
                               command=cerrar_error, bg="#FF69B4", fg="white", 
                               font=("Arial", 10, "bold"), padx=20, pady=5)
        btn_aceptar.pack(pady=10)
        btn_aceptar.focus()
        
        # Permitir cerrar con Enter o Escape
        ventana_error.bind('<Return>', lambda event: cerrar_error())
        ventana_error.bind('<Escape>', lambda event: cerrar_error())
        
        print(f"Error de impresión: {e}")

# 🖼️ Ventana principal con diseño femenino
ventana = tk.Tk()
ventana.title("💖 Variedades Marce - POS Femenino 🌸")
ventana.geometry("1000x700")
ventana.configure(bg="#FFB6C1")  # Rosa claro más femenino

# 🎨 Configurar estilo para los widgets
style = ttk.Style()
style.theme_use('clam')
style.configure('Feminine.TLabel', 
                background='#FFB6C1', 
                foreground='#8B0054',  # Rosa oscuro
                font=('Arial', 10))
style.configure('Header.TLabel', 
                background='#FFB6C1', 
                foreground='#8B0054', 
                font=('Arial', 14, 'bold'))
style.configure('Feminine.TButton',
                background='#FF69B4',  # Rosa más vivo
                foreground='white',
                font=('Arial', 9, 'bold'))

# 🧮 Variables
documento = tk.StringVar()
codigo_entrada = tk.StringVar()
cantidad = tk.IntVar(value=1)
total_general = tk.DoubleVar(value=0.0)
factura_num = datetime.now().strftime("%Y%m%d%H%M%S")  # Número único basado en fecha/hora

# 🎀 Encabezado con diseño femenino
fecha_actual = datetime.now().strftime("%d-%m-%Y")
hora_actual = datetime.now().strftime("%H:%M:%S")

header_frame = tk.Frame(ventana, bg="#FF1493", height=80)  # Rosa fucsia para header
header_frame.grid(row=0, column=0, columnspan=6, sticky="ew", padx=5, pady=5)
header_frame.grid_propagate(False)

tk.Label(header_frame, text="💖 VARIEDADES MARCE - POS 🌸", 
         font=("Arial", 18, "bold"), bg="#FF1493", fg="white").pack(pady=15)

# Información de factura
info_frame = tk.Frame(ventana, bg="#FFB6C1")
info_frame.grid(row=1, column=0, columnspan=6, sticky="ew", padx=10, pady=5)

tk.Label(info_frame, text=f"🧾 Factura: {factura_num}", 
         font=("Arial", 10), bg="#FFB6C1", fg="#8B0054").grid(row=0, column=0, padx=10)
tk.Label(info_frame, text=f"📅 Fecha: {fecha_actual}", 
         font=("Arial", 10), bg="#FFB6C1", fg="#8B0054").grid(row=0, column=1, padx=10)
tk.Label(info_frame, text=f"🕒 Hora: {hora_actual}", 
         font=("Arial", 10), bg="#FFB6C1", fg="#8B0054").grid(row=0, column=2, padx=10)

# 🪪 Documento y escaneo con marco rosa
input_frame = tk.Frame(ventana, bg="#FFC0CB", relief="raised", bd=2)  # Rosa pastel
input_frame.grid(row=2, column=0, columnspan=6, sticky="ew", padx=10, pady=10)

tk.Label(input_frame, text="👤 Documento Cliente:", 
         font=("Arial", 10, "bold"), bg="#FFC0CB", fg="#8B0054").grid(row=0, column=0, padx=10, pady=10, sticky="w")
entry_doc = tk.Entry(input_frame, textvariable=documento, width=25, font=("Arial", 10))
entry_doc.grid(row=0, column=1, padx=10, pady=10)

tk.Label(input_frame, text="🔢 Código producto:", 
         font=("Arial", 10, "bold"), bg="#FFC0CB", fg="#8B0054").grid(row=0, column=2, padx=10, pady=10)
entry_codigo = tk.Entry(input_frame, textvariable=codigo_entrada, width=20, font=("Arial", 10))
entry_codigo.grid(row=0, column=3, padx=10, pady=10)

# 🧾 Tabla de productos con estilo femenino
tabla_frame = tk.Frame(ventana, bg="#FFB6C1")
tabla_frame.grid(row=4, column=0, columnspan=6, padx=10, pady=10, sticky="ew")

tk.Label(tabla_frame, text="🛍️ Productos en el carrito:", 
         font=("Arial", 12, "bold"), bg="#FFB6C1", fg="#8B0054").pack(pady=5)

tabla = ttk.Treeview(tabla_frame, columns=("Producto", "Precio", "Cantidad", "Total"), show="headings", height=10)
for col in ("Producto", "Precio", "Cantidad", "Total"):
    tabla.heading(col, text=col)
    tabla.column(col, width=200, anchor="center")
tabla.pack(padx=10, pady=5)

# 🔍 Buscar producto
def buscar_producto():
    ventana_busqueda = tk.Toplevel()
    ventana_busqueda.title("🔎 Buscar producto")
    ventana_busqueda.geometry("700x450")
    ventana_busqueda.configure(bg="#FFB6C1")

    filtro = tk.StringVar()
    tk.Label(ventana_busqueda, text="🔍 Buscar por código o nombre:", 
             bg="#FFB6C1", fg="#8B0054", font=("Arial", 12, "bold")).pack(pady=10)
    entry_busqueda = tk.Entry(ventana_busqueda, textvariable=filtro, width=50, font=("Arial", 10))
    entry_busqueda.pack(pady=5)

    columnas = ("Código", "Nombre", "Stock", "Precio")
    lista = ttk.Treeview(ventana_busqueda, columns=columnas, show="headings", height=15)
    for col in columnas:
        lista.heading(col, text=col)
        lista.column(col, width=150, anchor="center")
    lista.pack(padx=10, pady=10)

    def cargar_productos(filtrar=""):
        lista.delete(*lista.get_children())
        for codigo, nombre, stock, precio in obtener_productos():
            texto = f"{codigo} {nombre}".lower()
            if not filtrar or filtrar.lower() in texto:
                lista.insert("", tk.END, values=(codigo, nombre, stock, formato_peso(precio)))

    cargar_productos()

    def actualizar_busqueda(*args):
        cargar_productos(filtro.get())

    filtro.trace("w", actualizar_busqueda)

    def seleccionar():
        seleccionado = lista.focus()
        if not seleccionado:
            messagebox.showwarning("⚠️ Selección", "Por favor selecciona un producto")
            return
        valores = lista.item(seleccionado)["values"]
        nombre = valores[1]
        precio = limpiar_precio(valores[3])
        agregar_a_ticket(nombre, precio, 1)
        ventana_busqueda.destroy()

    btn_frame = tk.Frame(ventana_busqueda, bg="#FFB6C1")
    btn_frame.pack(pady=10)
    
    btn_seleccionar = tk.Button(btn_frame, text="✨ Seleccionar Producto", 
                               command=seleccionar, bg="#FF69B4", fg="white", 
                               font=("Arial", 10, "bold"), padx=20)
    btn_seleccionar.pack()

# 🛒 Agregar producto al ticket
def agregar_a_ticket(nombre, precio, cantidad):
    total = round(precio * cantidad, 2)
    tabla.insert("", tk.END, values=(nombre, formato_peso(precio), cantidad, formato_peso(total)))
    total_general.set(total_general.get() + total)
    actualizar_total()

# 📲 Escaneo por código
def escanear_codigo():
    codigo = codigo_entrada.get().strip()
    if not codigo:
        messagebox.showwarning("⚠️ Código vacío", "Ingresa un código para buscar")
        return
        
    productos = obtener_productos()
    for prod in productos:
        if prod[0] == codigo:
            agregar_a_ticket(prod[1], prod[3], 1)
            codigo_entrada.set("")
            entry_codigo.focus()
            return
    messagebox.showerror("❌ No encontrado", "Producto no existe en el inventario.")
    codigo_entrada.set("")

# Vincular Enter al campo de código
entry_codigo.bind('<Return>', lambda event: escanear_codigo())

# 🗑️ Eliminar producto
def eliminar_seleccionado():
    seleccionado = tabla.focus()
    if not seleccionado:
        messagebox.showwarning("⚠️ Selección", "Selecciona un producto para eliminar")
        return
    valores = tabla.item(seleccionado)["values"]
    total_fila = limpiar_precio(valores[3])
    total_general.set(total_general.get() - total_fila)
    tabla.delete(seleccionado)
    actualizar_total()

# 💸 Total a pagar con diseño destacado
total_frame = tk.Frame(ventana, bg="#FF1493", relief="raised", bd=3)
total_frame.grid(row=5, column=0, columnspan=6, sticky="ew", padx=10, pady=10)

tk.Label(total_frame, text="💸 TOTAL A PAGAR:", 
         font=("Arial", 16, "bold"), bg="#FF1493", fg="white").pack(side="left", padx=20, pady=10)
total_label = tk.Label(total_frame, text=formato_peso(total_general.get()), 
                      font=("Arial", 18, "bold"), bg="#FF1493", fg="yellow")
total_label.pack(side="right", padx=20, pady=10)

def actualizar_total():
    total_label.config(text=formato_peso(total_general.get()))

# 🎀 Botones con diseño femenino
button_frame = tk.Frame(ventana, bg="#FFB6C1")
button_frame.grid(row=3, column=0, columnspan=6, pady=10)

btn_buscar = tk.Button(button_frame, text="🔍 Buscar Producto", command=buscar_producto,
                      bg="#FF69B4", fg="white", font=("Arial", 10, "bold"), padx=15, pady=5)
btn_buscar.grid(row=0, column=0, padx=10)

btn_escanear = tk.Button(button_frame, text="📲 Escanear", command=escanear_codigo,
                        bg="#FF69B4", fg="white", font=("Arial", 10, "bold"), padx=15, pady=5)
btn_escanear.grid(row=0, column=1, padx=10)

btn_eliminar = tk.Button(button_frame, text="🗑️ Eliminar", command=eliminar_seleccionado,
                        bg="#DC143C", fg="white", font=("Arial", 10, "bold"), padx=15, pady=5)
btn_eliminar.grid(row=0, column=2, padx=10)

# 💳 Pagar con impresión automática
def pagar():
    if not documento.get().strip():
        messagebox.showerror("⚠️ Documento requerido", "Debes ingresar el número de documento del cliente.")
        return
    
    if total_general.get() <= 0:
        messagebox.showerror("⚠️ Sin productos", "Agrega productos antes de realizar el pago.")
        return

    ventana_pago = tk.Toplevel()
    ventana_pago.title("💳 Procesar Pago")
    ventana_pago.geometry("400x300")
    ventana_pago.configure(bg="#FFB6C1")

    # Hacer la ventana modal
    ventana_pago.transient(ventana)
    ventana_pago.grab_set()

    tk.Label(ventana_pago, text="💖 PROCESAR PAGO 💖", 
             font=("Arial", 16, "bold"), bg="#FFB6C1", fg="#8B0054").pack(pady=15)

    tk.Label(ventana_pago, text="💸 Monto a pagar:", 
             font=("Arial", 12, "bold"), bg="#FFB6C1", fg="#8B0054").pack(pady=5)
    tk.Label(ventana_pago, text=formato_peso(total_general.get()), 
             font=("Arial", 14, "bold"), bg="#FFB6C1", fg="#FF1493").pack(pady=5)

    tk.Label(ventana_pago, text="💵 Efectivo recibido:", 
             font=("Arial", 12, "bold"), bg="#FFB6C1", fg="#8B0054").pack(pady=5)
    efectivo = tk.DoubleVar()
    entry_efectivo = tk.Entry(ventana_pago, textvariable=efectivo, font=("Arial", 12), width=20)
    entry_efectivo.pack(pady=5)
    entry_efectivo.focus()

    def calcular_cambio():
        try:
            recibido = efectivo.get()
            total = total_general.get()
            
            if recibido < total:
                messagebox.showwarning("💸 Efectivo insuficiente", 
                                     f"Faltan: {formato_peso(total - recibido)}")
                return

            vuelto = recibido - total

            # Recopilar productos para la factura
            productos_vendidos = []
            for item in tabla.get_children():
                nombre, precio_txt, cantidad, _ = tabla.item(item)["values"]
                precio = limpiar_precio(precio_txt)
                productos_vendidos.append((nombre, precio, int(cantidad)))

            # Mostrar resumen
            resultado = f"""
💖 VENTA COMPLETADA 💖

🧾 Factura: {factura_num}
📅 {fecha_actual} 🕒 {hora_actual}
👤 Cliente: {documento.get()}

💸 Total: {formato_peso(total)}
💵 Recibido: {formato_peso(recibido)}
💰 Cambio: {formato_peso(vuelto)}

🌸 ¡Gracias por tu compra! 🌸
"""
            messagebox.showinfo("✅ Pago Completado", resultado)

            # Imprimir factura automáticamente
            imprimir_factura_termica(
                documento_cliente=documento.get(),
                usuario="Vendedora",
                productos=productos_vendidos,
                total_general=total,
                factura_num=factura_num,
                fecha=fecha_actual,
                hora=hora_actual
            )

            # Limpiar formulario para nueva venta
            limpiar_formulario()
            ventana_pago.destroy()

        except tk.TclError:
            messagebox.showerror("❌ Error", "Ingresa un monto válido")

    # Vincular Enter para procesar pago
    entry_efectivo.bind('<Return>', lambda event: calcular_cambio())

    btn_pagar = tk.Button(ventana_pago, text="✅ Completar Pago e Imprimir", 
                         command=calcular_cambio, bg="#32CD32", fg="white", 
                         font=("Arial", 12, "bold"), padx=20, pady=10)
    btn_pagar.pack(pady=20)

def limpiar_formulario():
    """Limpiar el formulario después de una venta"""
    global factura_num
    documento.set("")
    codigo_entrada.set("")
    total_general.set(0.0)
    factura_num = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Limpiar tabla
    for item in tabla.get_children():
        tabla.delete(item)
    
    actualizar_total()
    # Actualizar número de factura en pantalla
    info_frame.grid_forget()
    info_frame.grid(row=1, column=0, columnspan=6, sticky="ew", padx=10, pady=5)
    
    for widget in info_frame.winfo_children():
        widget.destroy()
        
    tk.Label(info_frame, text=f"🧾 Factura: {factura_num}", 
             font=("Arial", 10), bg="#FFB6C1", fg="#8B0054").grid(row=0, column=0, padx=10)
    tk.Label(info_frame, text=f"📅 Fecha: {datetime.now().strftime('%d-%m-%Y')}", 
             font=("Arial", 10), bg="#FFB6C1", fg="#8B0054").grid(row=0, column=1, padx=10)
    tk.Label(info_frame, text=f"🕒 Hora: {datetime.now().strftime('%H:%M:%S')}", 
             font=("Arial", 10), bg="#FFB6C1", fg="#8B0054").grid(row=0, column=2, padx=10)

# Botón de pago principal
payment_frame = tk.Frame(ventana, bg="#FFB6C1")
payment_frame.grid(row=6, column=0, columnspan=6, pady=20)

btn_pagar_main = tk.Button(payment_frame, text="💳 PROCESAR PAGO E IMPRIMIR", 
                          command=pagar, bg="#32CD32", fg="white", 
                          font=("Arial", 14, "bold"), padx=30, pady=15)
btn_pagar_main.pack()

btn_nueva_venta = tk.Button(payment_frame, text="🆕 Nueva Venta", 
                           command=limpiar_formulario, bg="#FF8C00", fg="white", 
                           font=("Arial", 10, "bold"), padx=20, pady=5)
btn_nueva_venta.pack(pady=10)

# Configurar el foco inicial
entry_doc.focus()

# Centrar ventana
ventana.update_idletasks()
width = ventana.winfo_width()
height = ventana.winfo_height()
x = (ventana.winfo_screenwidth() // 2) - (width // 2)
y = (ventana.winfo_screenheight() // 2) - (height // 2)
ventana.geometry(f"{width}x{height}+{x}+{y}")

ventana.mainloop()