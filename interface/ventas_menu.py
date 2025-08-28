# ====================================================================================
#   IMPORTS Y CONFIGURACIÓN INICIAL
# ====================================================================================

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import os

# --- Importación opcional de la biblioteca para impresora térmica ---
# Asegúrate de que las bibliotecas necesarias estén instaladas:
# pip install escpos-python
try:
    from escpos.printer import Usb
except ImportError:
    # Este bloque maneja el caso en que la biblioteca no está instalada,
    # permitiendo que la aplicación se ejecute sin la funcionalidad de impresión.
    messagebox.showwarning("Advertencia", "La biblioteca 'escpos-python' no está instalada. La funcionalidad de impresión no estará disponible.")
    # Crea una clase simulada para evitar errores en el resto del código
    class Usb:
        def __init__(self, *args, **kwargs):
            pass
        def set(self, *args, **kwargs):
            pass
        def text(self, *args, **kwargs):
            pass
        def cut(self):
            pass

# ====================================================================================
#   CLASE PRINCIPAL DE LA APLICACIÓN
# ====================================================================================

class App:
    def __init__(self, ventana):
        """
        Constructor de la clase App. Inicializa la ventana principal y sus componentes.
        """
        self.ventana = ventana
        self.ventana.title("💖 Variedades Marce - POS Femenino 🌸")
        self.ventana.geometry("850x700")
        self.ventana.configure(bg="#FFB6C1")

        # 🎨 Configurar estilo para los widgets de la aplicación
        self.configurar_estilos()

        # 🧮 Variables de control para la aplicación
        self.documento = tk.StringVar()
        self.codigo_entrada = tk.StringVar()
        self.total_general = tk.DoubleVar(value=0.0)
        self.factura_num = self.generar_numero_factura()
        self.productos_inventario = self.obtener_productos()
        self.productos_en_carrito = {}  # Diccionario para gestionar productos en el carrito: {codigo: (nombre, precio, cantidad)}

        # 🎀 Construir la interfaz de usuario
        self.crear_widgets()

        # 🔄 Actualizar la hora en el encabezado
        self.actualizar_hora()

        # Configurar el foco inicial en la entrada de documento
        self.entry_doc.focus()

        # Centrar la ventana en la pantalla
        self.ventana.update_idletasks()
        width = self.ventana.winfo_width()
        height = self.ventana.winfo_height()
        x = (self.ventana.winfo_screenwidth() // 2) - (width // 2)
        y = (self.ventana.winfo_screenheight() // 2) - (height // 2)
        self.ventana.geometry(f"{width}x{height}+{x}+{y}")

    def configurar_estilos(self):
        """
        Configura los estilos personalizados para los widgets de `ttk`.
        """
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Feminine.TLabel',
                        background='#FFB6C1',
                        foreground='#8B0054',
                        font=('Arial', 10))
        style.configure('Header.TLabel',
                        background='#FFB6C1',
                        foreground='#8B0054',
                        font=('Arial', 14, 'bold'))
        style.configure('Feminine.TButton',
                        background='#FF69B4',
                        foreground='white',
                        font=('Arial', 9, 'bold'))
        style.configure('Treeview.Heading',
                        background='#FF69B4',
                        foreground='white',
                        font=('Arial', 10, 'bold'))
        style.configure('Treeview',
                        background='#FFFFFF',
                        foreground='#8B0054',
                        fieldbackground='#FFFFFF')

    def generar_numero_factura(self):
        """Genera un número de factura único basado en la fecha y hora."""
        return datetime.now().strftime("%Y%m%d%H%M%S")

    def crear_widgets(self):
        """
        Crea y posiciona todos los widgets de la interfaz de usuario.
        """
        # 🎀 Encabezado con diseño femenino
        header_frame = tk.Frame(self.ventana, bg="#FF1493", height=80)
        header_frame.grid(row=0, column=0, columnspan=6, sticky="ew", padx=5, pady=5)
        header_frame.grid_propagate(False)

        tk.Label(header_frame, text="💖 VARIEDADES MARCE 🌸",
                 font=("Arial", 18, "bold"), bg="#FF1493", fg="white").pack(pady=15)

        # Información de factura
        self.info_frame = tk.Frame(self.ventana, bg="#FFB6C1")
        self.info_frame.grid(row=1, column=0, columnspan=6, sticky="ew", padx=10, pady=5)
        self.lbl_factura = tk.Label(self.info_frame, text=f"🧾 Factura: {self.factura_num}",
                                     font=("Arial", 10), bg="#FFB6C1", fg="#8B0054")
        self.lbl_factura.grid(row=0, column=0, padx=10)
        self.lbl_fecha = tk.Label(self.info_frame, text="",
                                  font=("Arial", 10), bg="#FFB6C1", fg="#8B0054")
        self.lbl_fecha.grid(row=0, column=1, padx=10)
        self.lbl_hora = tk.Label(self.info_frame, text="",
                                 font=("Arial", 10), bg="#FFB6C1", fg="#8B0054")
        self.lbl_hora.grid(row=0, column=2, padx=10)

        # 🪪 Documento y escaneo con marco rosa
        input_frame = tk.Frame(self.ventana, bg="#FFC0CB", relief="raised", bd=2)
        input_frame.grid(row=2, column=0, columnspan=6, sticky="ew", padx=10, pady=10)

        tk.Label(input_frame, text="👤 Documento Cliente:",
                 font=("Arial", 10, "bold"), bg="#FFC0CB", fg="#8B0054").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.entry_doc = tk.Entry(input_frame, textvariable=self.documento, width=25, font=("Arial", 10))
        self.entry_doc.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(input_frame, text="🔢 Código producto:",
                 font=("Arial", 10, "bold"), bg="#FFC0CB", fg="#8B0054").grid(row=0, column=2, padx=10, pady=10)
        self.entry_codigo = tk.Entry(input_frame, textvariable=self.codigo_entrada, width=20, font=("Arial", 10))
        self.entry_codigo.grid(row=0, column=3, padx=10, pady=10)
        self.entry_codigo.bind('<Return>', lambda event: self.escanear_codigo())

        # 🧾 Tabla de productos con estilo femenino
        tabla_frame = tk.Frame(self.ventana, bg="#FFB6C1")
        tabla_frame.grid(row=4, column=0, columnspan=6, padx=10, pady=10, sticky="ew")

        tk.Label(tabla_frame, text="🛍️ Productos en el carrito:",
                 font=("Arial", 12, "bold"), bg="#FFB6C1", fg="#8B0054").pack(pady=5)

        self.tabla = ttk.Treeview(tabla_frame, columns=("Producto", "Precio", "Cantidad", "Total"), show="headings", height=10)
        for col in ("Producto", "Precio", "Cantidad", "Total"):
            self.tabla.heading(col, text=col)
            self.tabla.column(col, width=200, anchor="center")
        self.tabla.pack(padx=10, pady=5)

        # 💸 Total a pagar con diseño destacado
        total_frame = tk.Frame(self.ventana, bg="#FF1493", relief="raised", bd=3)
        total_frame.grid(row=5, column=0, columnspan=6, sticky="ew", padx=10, pady=10)

        tk.Label(total_frame, text="💸 TOTAL A PAGAR:",
                 font=("Arial", 16, "bold"), bg="#FF1493", fg="white").pack(side="left", padx=20, pady=10)
        self.total_label = tk.Label(total_frame, text=self.formato_peso(self.total_general.get()),
                                     font=("Arial", 18, "bold"), bg="#FF1493", fg="yellow")
        self.total_label.pack(side="right", padx=20, pady=10)

        # 🎀 Botones con diseño femenino
        button_frame = tk.Frame(self.ventana, bg="#FFB6C1")
        button_frame.grid(row=3, column=0, columnspan=6, pady=10)

        btn_buscar = tk.Button(button_frame, text="🔍 Buscar Producto", command=self.buscar_producto,
                               bg="#FF69B4", fg="white", font=("Arial", 10, "bold"), padx=15, pady=5)
        btn_buscar.grid(row=0, column=0, padx=10)

        btn_escanear = tk.Button(button_frame, text="📲 Escanear", command=self.escanear_codigo,
                                 bg="#FF69B4", fg="white", font=("Arial", 10, "bold"), padx=15, pady=5)
        btn_escanear.grid(row=0, column=1, padx=10)

        btn_eliminar = tk.Button(button_frame, text="🗑️ Eliminar", command=self.eliminar_seleccionado,
                                 bg="#DC143C", fg="white", font=("Arial", 10, "bold"), padx=15, pady=5)
        btn_eliminar.grid(row=0, column=2, padx=10)
        
        # Botón de pago principal
        payment_frame = tk.Frame(self.ventana, bg="#FFB6C1")
        payment_frame.grid(row=6, column=0, columnspan=6, pady=20)
        
        btn_pagar_main = tk.Button(payment_frame, text="💳 PROCESAR PAGO E IMPRIMIR",
                                   command=self.pagar, bg="#32CD32", fg="white",
                                   font=("Arial", 14, "bold"), padx=30, pady=15)
        btn_pagar_main.pack()
        
        btn_nueva_venta = tk.Button(payment_frame, text="🆕 Nueva Venta",
                                    command=self.limpiar_formulario, bg="#FF8C00", fg="white",
                                    font=("Arial", 10, "bold"), padx=20, pady=5)
        btn_nueva_venta.pack(pady=10)

    # ====================================================================================
    #   FUNCIONES DE CONEXIÓN Y UTILIDADES
    # ====================================================================================
    
    def obtener_productos(self):
        """
        Obtiene todos los productos del inventario con sus datos principales.
        """
        # La ruta a la base de datos se mantiene igual
        base_dir = os.path.dirname(__file__)
        ruta_db = os.path.join(base_dir, '..', 'database', 'ventas.db')
        try:
            with sqlite3.connect(ruta_db) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT codigo, nombre, stock, precio FROM productos")
                productos = cursor.fetchall()
                return productos
        except Exception as e:
            messagebox.showerror("Error de conexión", f"No se pudo abrir la base de datos:\n{e}")
            return []

    def formato_peso(self, valor):
        """
        Formatea un número a pesos colombianos.
        """
        return f"${int(valor):,.0f} COP"

    def limpiar_precio(self, texto):
        """
        Limpia un texto de formato de precio para convertirlo a un número flotante.
        Esta función está diseñada para el formato de pesos colombianos sin decimales.
        """
        # Elimina el signo de dólar, el sufijo COP y las comas
        texto = texto.replace("$", "").replace("COP", "").replace(",", "").strip()
        try:
            return float(texto)
        except ValueError:
            return 0.0

    def guardar_venta_db(self, documento_cliente, total_venta):
        """
        Guarda una nueva venta en la tabla 'ventas' de la base de datos,
        usando las columnas 'fecha_venta' y 'hora_venta'.
        """
        base_dir = os.path.dirname(__file__)
        ruta_db = os.path.join(base_dir, '..', 'database', 'ventas.db')
        try:
            with sqlite3.connect(ruta_db) as conn:
                cursor = conn.cursor()
                fecha_venta = datetime.now().strftime("%Y-%m-%d")
                hora_venta = datetime.now().strftime("%H:%M:%S")

                cursor.execute(
                    "INSERT INTO ventas (fecha_venta, hora_venta, documento_cliente, total_venta) VALUES (?, ?, ?, ?)",
                    (fecha_venta, hora_venta, documento_cliente, total_venta)
                )
                id_venta = cursor.lastrowid
                print(f"DEBUG: Venta principal guardada con ID: {id_venta}")
                conn.commit()
                return id_venta
        except Exception as e:
            messagebox.showerror("Error de base de datos", f"No se pudo guardar la venta:\n{e}")
            return None

    def guardar_detalle_ventas_db(self, id_venta, productos_vendidos):
        """
        Guarda el detalle de cada producto vendido en la tabla 'detalle_ventas'
        y actualiza el stock en la tabla 'productos'.
        """
        base_dir = os.path.dirname(__file__)
        ruta_db = os.path.join(base_dir, '..', 'database', 'ventas.db')
        try:
            with sqlite3.connect(ruta_db) as conn:
                cursor = conn.cursor()
                
                for codigo_producto, nombre_producto, precio_unitario, cantidad, subtotal in productos_vendidos:
                    # Insertar en la tabla 'detalle_ventas'
                    cursor.execute(
                        "INSERT INTO detalle_ventas (id_venta, codigo_producto, nombre_producto, precio_unitario, cantidad, subtotal, codigo) VALUES (?, ?, ?, ?, ?, ?)", 
                        (id_venta, codigo_producto, nombre_producto, precio_unitario, cantidad, subtotal)
                    )
                    
                    # Actualizar el stock del producto de forma flexible
                    cursor.execute("UPDATE productos SET stock = stock - ? WHERE codigo = ?", (cantidad, codigo_producto))
                    rows_updated = cursor.rowcount

                    if rows_updated == 0:
                        codigo_formateado = codigo_producto.zfill(5)
                        cursor.execute("UPDATE productos SET stock = stock - ? WHERE codigo = ?", (cantidad, codigo_formateado))
                        rows_updated = cursor.rowcount
                    
                    if rows_updated == 0:
                        print(f"ADVERTENCIA: No se encontró ningún producto con el código '{codigo_producto}' para actualizar.")

                conn.commit()
                return True
        except Exception as e:
            messagebox.showerror("Error de base de datos", f"No se pudo guardar el detalle de la venta:\n{e}")
            return False
        
    def actualizar_stock_db(productos_vendidos):
        ruta_db = os.path.join(base_dir, '..', 'database', 'ventas.db')
        with sqlite3.connect(ruta_db) as conexion:
            cursor=conexion.cursor()
            for producto in productos_vendidos:
                codigo = producto ['codigo']
                cantidad_vendida = producto ['cantidad']

                #obtener stock actual📌
                cursor.execute("SELECT stock FROM productos")
                resultado=cursor.fetchone()
                if resultado:
                   stock_actual = resultado[0]
                   nuevo_stock = stock_actual - cantidad_vendida

                   #actualizar stock
                   cursor.execute("UPDATE productos SET stock = ? WHERE codigo = ?", (nuevo_stock, codigo))
        

    def imprimir_factura_termica(self, documento_cliente, usuario, productos, total_general, factura_num, fecha, hora):
        """
        Imprime una factura en una impresora térmica compatible.
        """
        try:
            # IDs de impresoras comunes para probar la conexión
            ids_impresoras = [
                (0x0fe6, 0x811e), (0x04b8, 0x0202), (0x04b8, 0x0e15),
                (0x154f, 0x154f), (0x1fc9, 0x2016), (0x0483, 0x5743)
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

            p.text("Producto           Cant  Precio\n")
            p.text("-" * 32 + "\n")

            total_items = 0
            for nombre, precio, cantidad in productos:
                subtotal = precio * cantidad
                total_items += cantidad
                nombre_corto = nombre[:15].ljust(15)
                # Formato para la impresión de la línea de cada producto
                p.text(f"{nombre_corto} {cantidad:>2}x ${precio:>6,.0f}\n")
                p.text(f"      Subtotal: ${subtotal:>8,.0f}\n")

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
            self.mostrar_error_impresion(e)
            print(f"Error de impresión: {e}")
    
    def mostrar_error_impresion(self, e):
        """
        Crea una ventana de error personalizada para la impresora.
        """
        ventana_error = tk.Toplevel(self.ventana)
        ventana_error.title("❌ Error de impresión")
        ventana_error.geometry("500x250")
        ventana_error.configure(bg="#FFB6C1")
        ventana_error.grab_set()

        ventana_error.update_idletasks()
        x = (self.ventana.winfo_screenwidth() // 2) - (250)
        y = (self.ventana.winfo_screenheight() // 2) - (125)
        ventana_error.geometry(f"500x250+{x}+{y}")

        tk.Label(ventana_error, text="❌ ERROR DE IMPRESIÓN",
                 font=("Arial", 14, "bold"), bg="#FFB6C1", fg="#8B0054").pack(pady=10)
        tk.Label(ventana_error, text="No se pudo conectar con la impresora:",
                 font=("Arial", 10), bg="#FFB6C1", fg="#8B0054").pack(pady=5)

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
        ventana_error.bind('<Return>', lambda event: cerrar_error())
        ventana_error.bind('<Escape>', lambda event: cerrar_error())

    # ====================================================================================
    #   FUNCIONES DE LA INTERFAZ DE USUARIO
    # ====================================================================================

    def actualizar_total(self):
        """
        Actualiza el label del total de la venta.
        """
        self.total_label.config(text=self.formato_peso(self.total_general.get()))

    def actualizar_hora(self):
        """
        Actualiza la hora y la fecha en la interfaz de usuario cada segundo.
        """
        ahora = datetime.now()
        self.lbl_fecha.config(text=f"📅 Fecha: {ahora.strftime('%d-%m-%Y')}")
        self.lbl_hora.config(text=f"🕒 Hora: {ahora.strftime('%H:%M:%S')}")
        self.ventana.after(1000, self.actualizar_hora)

    def buscar_producto(self):
        """
        Abre una nueva ventana para buscar productos y agregarlos a la venta.
        """
        ventana_busqueda = tk.Toplevel(self.ventana)
        ventana_busqueda.title("🔎 Buscar producto")
        ventana_busqueda.geometry("700x500")
        ventana_busqueda.configure(bg="#FFB6C1")
        ventana_busqueda.grab_set()

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
            for codigo, nombre, stock, precio in self.productos_inventario:
                texto = f"{codigo} {nombre}".lower()
                if not filtrar or filtrar.lower() in texto:
                    lista.insert("", tk.END, values=(codigo, nombre, stock, self.formato_peso(precio)))

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
            codigo = valores[0]
            nombre = valores[1]
            precio = self.limpiar_precio(valores[3])
            self.agregar_a_ticket(codigo, nombre, precio, 1)
            ventana_busqueda.destroy()

        btn_frame = tk.Frame(ventana_busqueda, bg="#FFB6C1")
        btn_frame.pack(pady=10)
        
        btn_seleccionar = tk.Button(btn_frame, text="✨ Seleccionar Producto",
                                     command=seleccionar, bg="#FF69B4", fg="white",
                                     font=("Arial", 10, "bold"), padx=20)
        btn_seleccionar.pack()
        # Enlaza la tecla Enter a la función de selección
        ventana_busqueda.bind('<Return>', lambda event: seleccionar())
        entry_busqueda.focus()

    def agregar_a_ticket(self, codigo, nombre, precio, cantidad):
        """
        Agrega un producto al Treeview de la venta.
        Si el producto ya está en el carrito, actualiza la cantidad y el total.
        """
        # Buscar si el producto ya está en el carrito
        item_existente = None
        for item in self.tabla.get_children():
            values = self.tabla.item(item)["values"]
            # El código del producto se guarda como el último valor en el Treeview
            if values[-1] == codigo:
                item_existente = item
                break

        if item_existente:
            # Actualizar cantidad y total
            nombre_actual, precio_actual_txt, cantidad_actual, total_actual_txt = self.tabla.item(item_existente)["values"]
            nueva_cantidad = int(cantidad_actual) + cantidad
            nuevo_total = round(precio * nueva_cantidad, 2)
            self.tabla.item(item_existente, values=(nombre, self.formato_peso(precio), nueva_cantidad, self.formato_peso(nuevo_total), codigo))
            
            # Ajustar el total general
            self.total_general.set(self.total_general.get() + round(precio * cantidad, 2))
        else:
            # Agregar un nuevo producto
            total = round(precio * cantidad, 2)
            # Se agrega el código como un valor oculto en la última columna
            self.tabla.insert("", tk.END, values=(nombre, self.formato_peso(precio), cantidad, self.formato_peso(total), codigo))
            self.total_general.set(self.total_general.get() + total)
            
        self.actualizar_total()

    def escanear_codigo(self):
        """
        Busca un producto por su código y lo agrega a la venta si existe.
        """
        codigo = self.codigo_entrada.get().strip()
        if not codigo:
            messagebox.showwarning("⚠️ Código vacío", "Ingresa un código para buscar")
            return
        
        producto_encontrado = None
        for prod in self.productos_inventario:
            # Compara el código sin formato y el código con ceros a la izquierda
            if str(prod[0]) == codigo or str(prod[0]).zfill(5) == codigo:
                producto_encontrado = prod
                break

        if producto_encontrado:
            # prod[0]=codigo, prod[1]=nombre, prod[3]=precio
            self.agregar_a_ticket(str(producto_encontrado[0]), producto_encontrado[1], producto_encontrado[3], 1)
            self.codigo_entrada.set("")
            self.entry_codigo.focus()
        else:
            messagebox.showerror("❌ No encontrado", "Producto no existe en el inventario.")
            self.codigo_entrada.set("")

    def eliminar_seleccionado(self):
        """
        Elimina el producto seleccionado del Treeview de la venta.
        """
        seleccionado = self.tabla.focus()
        if not seleccionado:
            messagebox.showwarning("⚠️ Selección", "Selecciona un producto para eliminar")
            return
        valores = self.tabla.item(seleccionado)["values"]
        # El valor total de la fila está en la posición 3
        total_fila = self.limpiar_precio(valores[3])
        self.total_general.set(self.total_general.get() - total_fila)
        self.tabla.delete(seleccionado)
        self.actualizar_total()

    def pagar(self):
        """
        Abre una ventana para procesar el pago de la venta.
        """
        if not self.documento.get().strip():
            messagebox.showerror("⚠️ Documento requerido", "Debes ingresar el número de documento del cliente.")
            return
        
        if self.total_general.get() <= 0:
            messagebox.showerror("⚠️ Sin productos", "Agrega productos antes de realizar el pago.")
            return

        ventana_pago = tk.Toplevel(self.ventana)
        ventana_pago.title("💳 Procesar Pago")
        ventana_pago.geometry("400x300")
        ventana_pago.configure(bg="#FFB6C1")
        ventana_pago.grab_set()

        tk.Label(ventana_pago, text="💖 PROCESAR PAGO 💖",
                 font=("Arial", 16, "bold"), bg="#FFB6C1", fg="#8B0054").pack(pady=15)

        tk.Label(ventana_pago, text="💸 Monto a pagar:",
                 font=("Arial", 12, "bold"), bg="#FFB6C1", fg="#8B0054").pack(pady=5)
        tk.Label(ventana_pago, text=self.formato_peso(self.total_general.get()),
                 font=("Arial", 14, "bold"), bg="#FFB6C1", fg="#FF1493").pack(pady=5)

        tk.Label(ventana_pago, text="💵 Efectivo recibido:",
                 font=("Arial", 12, "bold"), bg="#FFB6C1", fg="#8B0054").pack(pady=5)
        efectivo = tk.DoubleVar()
        entry_efectivo = tk.Entry(ventana_pago, textvariable=efectivo, font=("Arial", 12), width=20)
        entry_efectivo.pack(pady=5)
        entry_efectivo.focus()

        def completar_venta():
            try:
                recibido = efectivo.get()
                total = self.total_general.get()
                
                if recibido < total:
                    messagebox.showwarning("💸 Efectivo insuficiente",
                                           f"Faltan: {self.formato_peso(total - recibido)}")
                    return

                vuelto = recibido - total
                
                # Guardar venta en la base de datos
                id_venta = self.guardar_venta_db(self.documento.get(), total)
                if not id_venta:
                    messagebox.showerror("Error", "No se pudo guardar la venta en la base de datos.")
                    return

                # Preparar los datos para el detalle y la impresión
                productos_vendidos_db = []
                productos_vendidos_print = []
                for item in self.tabla.get_children():
                    nombre, precio_txt, cantidad, subtotal_txt, codigo = self.tabla.item(item)["values"]
                    precio = self.limpiar_precio(precio_txt)
                    subtotal = self.limpiar_precio(subtotal_txt)
                    productos_vendidos_db.append((codigo, nombre, precio, int(cantidad), subtotal))
                    productos_vendidos_print.append((nombre, precio, int(cantidad)))

                # Guardar detalles y actualizar stock en la base de datos
                if not self.guardar_detalle_ventas_db(id_venta, productos_vendidos_db):
                    messagebox.showerror("Error", "No se pudieron guardar los detalles de la venta.")
                    return

                # Mostrar mensaje de venta completada con el vuelto
                resultado = f"""
💖 VENTA COMPLETADA 💖

🧾 Factura: {self.factura_num}
📅 {datetime.now().strftime('%d-%m-%Y')} 🕒 {datetime.now().strftime('%H:%M:%S')}
👤 Cliente: {self.documento.get()}

💸 Total: {self.formato_peso(total)}
💵 Recibido: {self.formato_peso(recibido)}
💰 Cambio: {self.formato_peso(vuelto)}

🌸 ¡Gracias por tu compra! 🌸
"""
                messagebox.showinfo("✅ Pago Completado", resultado)

                # Imprimir la factura
                self.imprimir_factura_termica(
                    documento_cliente=self.documento.get(),
                    usuario="Vendedora", # Puedes hacer esto dinámico si tienes un sistema de login
                    productos=productos_vendidos_print,
                    total_general=total,
                    factura_num=self.factura_num,
                    fecha=datetime.now().strftime('%d-%m-%Y'),
                    hora=datetime.now().strftime('%H:%M:%S')
                )

                # Limpiar el formulario y cerrar la ventana de pago
                self.limpiar_formulario()
                ventana_pago.destroy()

            except tk.TclError:
                messagebox.showerror("❌ Error", "Ingresa un monto válido")

        entry_efectivo.bind('<Return>', lambda event: completar_venta())

        btn_pagar = tk.Button(ventana_pago, text="✅ Completar Pago e Imprimir",
                              command=completar_venta, bg="#32CD32", fg="white",
                              font=("Arial", 12, "bold"), padx=20, pady=10)
        btn_pagar.pack(pady=20)
        
        # Enlaza la tecla Escape para cerrar la ventana de pago
        ventana_pago.bind('<Escape>', lambda event: ventana_pago.destroy())

    def limpiar_formulario(self):
        """
        Limpia el formulario después de una venta para empezar una nueva.
        """
        self.documento.set("")
        self.codigo_entrada.set("")
        self.total_general.set(0.0)
        self.factura_num = self.generar_numero_factura()
        
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        
        self.actualizar_total()
        self.lbl_factura.config(text=f"🧾 Factura: {self.factura_num}")
        self.entry_doc.focus()


if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    root.mainloop()
