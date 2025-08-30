# ====================================================================================
#   SISTEMA DE VENTAS - VARIEDADES MARCE - VERSIÓN MEJORADA
# ====================================================================================

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import os

# Configuración de impresión
try:
    from escpos.printer import Usb, Win32Raw
    import usb.core
    import usb.util
    IMPRESION_DISPONIBLE = True
except ImportError:
    messagebox.showwarning("Advertencia", "Bibliotecas de impresión no disponibles. Funcionalidad limitada.")
    IMPRESION_DISPONIBLE = False

class PrinterManager:
    """Manejador de impresoras con configuración automática"""
    
    def __init__(self):
        self.printer = None
        self.printer_type = None
        self.config_exitosa = None
    
    def conectar_impresora(self):
        """Conecta automáticamente usando el método que funcione"""
        # Configuraciones comunes de impresoras térmicas
        configs = [
            # DigitalPOS
            {"vid": 0x0fe6, "pid": 0x811e, "in_ep": 0x82, "out_ep": 0x01},
            {"vid": 0x0fe6, "pid": 0x811f, "in_ep": 0x82, "out_ep": 0x01},
            {"vid": 0x0fe6, "pid": 0x811d, "in_ep": 0x82, "out_ep": 0x01},
            # Gprinter GP-58
            {"vid": 0x0416, "pid": 0x5011, "in_ep": 0x82, "out_ep": 0x01},
            {"vid": 0x0416, "pid": 0x5011, "in_ep": 0x81, "out_ep": 0x02},
            # Epson
            {"vid": 0x04b8, "pid": 0x0202, "in_ep": 0x82, "out_ep": 0x01},
            {"vid": 0x04b8, "pid": 0x0e15, "in_ep": 0x82, "out_ep": 0x01},
        ]
        
        print("🔍 Detectando impresora...")
        
        # Intentar conexión USB directa
        devices = usb.core.find(find_all=True)
        for device in devices:
            if device.bDeviceClass == 7:  # Clase de impresora
                vid, pid = device.idVendor, device.idProduct
                print(f"📱 Probando impresora: VID={hex(vid)}, PID={hex(pid)}")
                
                # Probar configuraciones conocidas
                for config in configs:
                    if config["vid"] == vid and config["pid"] == pid:
                        if self._probar_config_usb(config):
                            return True
                
                # Probar configuración genérica
                config_generica = {"vid": vid, "pid": pid, "in_ep": 0x82, "out_ep": 0x01}
                if self._probar_config_usb(config_generica):
                    return True
        
        # Intentar conexión Windows
        return self._conectar_windows()
    
    def _probar_config_usb(self, config):
        """Prueba una configuración USB específica"""
        try:
            printer = Usb(
                idVendor=config["vid"],
                idProduct=config["pid"],
                timeout=5000,
                in_ep=config["in_ep"],
                out_ep=config["out_ep"]
            )
            
            # Test básico
            printer.text("")
            
            self.printer = printer
            self.printer_type = "USB"
            self.config_exitosa = config
            print(f"✅ Conexión USB exitosa: {hex(config['vid'])}:{hex(config['pid'])}")
            return True
            
        except Exception as e:
            print(f"❌ Config fallida: {str(e)[:30]}...")
            return False
    
    def _conectar_windows(self):
        """Intenta conexión usando driver Windows"""
        try:
            import win32print
            printers = [p[2] for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL)]
            
            if printers:
                printer = Win32Raw(printers[0])
                self.printer = printer
                self.printer_type = "Windows"
                print(f"✅ Conexión Windows: {printers[0]}")
                return True
                
        except Exception as e:
            print(f"❌ Error Windows: {e}")
            
        return False
    
    def imprimir_factura(self, factura_data):
        """Imprime la factura usando la conexión establecida"""
        if not self.printer:
            raise Exception("No hay impresora conectada")
        
        try:
            p = self.printer
            
            print(f"DEBUG PrinterManager: Iniciando impresión de factura {factura_data['factura']}")
            
            # LIMPIAR BUFFER ANTES DE IMPRIMIR
            try:
                if hasattr(p, '_raw'):
                    p._raw(b'\x1B\x40')  # Comando ESC @ para resetear impresora
            except:
                pass
            
            # Configurar impresora
            p.set(align='center', bold=True, double_width=False, double_height=False)
            p.text("VARIEDADES MARCE\n")
            p.set(align='center', bold=False)
            p.text("Centro de copiado y belleza\n")
            p.text("Cel: 300-123-4567\n")
            p.text("=" * 32 + "\n")

            # Información de la venta
            p.set(align='left', bold=False)
            p.text(f"Factura: {factura_data['factura']}\n")
            p.text(f"Fecha: {factura_data['fecha']}\n")
            p.text(f"Hora: {factura_data['hora']}\n")
            p.text(f"Cliente: {factura_data['cliente']}\n")
            p.text("-" * 32 + "\n")

            p.text("Producto           Cant  Precio\n")
            p.text("-" * 32 + "\n")

            # Productos - PROCESAR INMEDIATAMENTE
            total_items = 0
            for nombre, precio, cantidad in factura_data['productos']:
                subtotal = precio * cantidad
                total_items += cantidad
                nombre_corto = nombre[:15].ljust(15)
                p.text(f"{nombre_corto} {cantidad:>2}x ${precio:>6,.0f}\n")
                if cantidad > 1:  # Solo mostrar subtotal si cantidad > 1
                    p.text(f"      Subtotal: ${subtotal:>8,.0f}\n")

            # Total
            p.text("-" * 32 + "\n")
            p.text(f"Total Items: {total_items}\n")
            p.set(bold=True)
            p.text(f"TOTAL: ${factura_data['total']:>16,.0f}\n")
            p.set(bold=False)
            p.text("=" * 32 + "\n")
            
            # Footer
            p.set(align='center')
            p.text("Gracias por tu compra!\n")
            p.text("Vuelve pronto\n")
            p.text("\n\n")
            
            # FORZAR CORTE E IMPRESIÓN INMEDIATA
            p.cut()
            
            # FLUSH/FINALIZAR INMEDIATAMENTE
            try:
                if hasattr(p, 'close'):
                    # No cerrar completamente, solo flush
                    pass
                # Comando para asegurar que se procese todo
                if hasattr(p, '_raw'):
                    p._raw(b'\n')  # Línea extra para asegurar procesamiento
            except:
                pass
                
            print(f"DEBUG PrinterManager: Factura {factura_data['factura']} enviada a impresora")
            
            return True
            
        except Exception as e:
            raise Exception(f"Error al imprimir: {str(e)}")

class App:
    def __init__(self, ventana):
        self.ventana = ventana
        self.setup_ventana()
        self.setup_variables()
        self.setup_datos()
        self.crear_interfaz()
        self.configurar_eventos()
        
        # Inicializar impresora
        self.printer_manager = PrinterManager() if IMPRESION_DISPONIBLE else None
        self.impresora_conectada = False
        
        # Conectar impresora al inicio
        if self.printer_manager:
            self.conectar_impresora_async()

    def setup_ventana(self):
        """Configuración inicial de la ventana"""
        self.ventana.title("💖 Variedades Marce - POS 🌸")
        self.ventana.geometry("850x700")
        self.ventana.configure(bg="#FFB6C1")
        
        # Centrar ventana
        self.ventana.update_idletasks()
        width, height = 850, 700
        x = (self.ventana.winfo_screenwidth() // 2) - (width // 2)
        y = (self.ventana.winfo_screenheight() // 2) - (height // 2)
        self.ventana.geometry(f"{width}x{height}+{x}+{y}")
        
        # Configurar estilos
        self.setup_estilos()

    def setup_estilos(self):
        """Configuración de estilos TTK"""
        style = ttk.Style()
        style.theme_use('clam')
        
        estilos = {
            'Feminine.TLabel': {'background': '#FFB6C1', 'foreground': '#8B0054', 'font': ('Arial', 10)},
            'Header.TLabel': {'background': '#FFB6C1', 'foreground': '#8B0054', 'font': ('Arial', 14, 'bold')},
            'Feminine.TButton': {'background': '#FF69B4', 'foreground': 'white', 'font': ('Arial', 9, 'bold')},
            'Treeview.Heading': {'background': '#FF69B4', 'foreground': 'white', 'font': ('Arial', 10, 'bold')},
            'Treeview': {'background': '#FFFFFF', 'foreground': '#8B0054', 'fieldbackground': '#FFFFFF'}
        }
        
        for nombre, config in estilos.items():
            style.configure(nombre, **config)

    def setup_variables(self):
        """Inicialización de variables de control"""
        self.documento = tk.StringVar()
        self.codigo_entrada = tk.StringVar()
        self.total_general = tk.DoubleVar(value=0.0)
        self.factura_num = datetime.now().strftime("%Y%m%d%H%M%S")

    def setup_datos(self):
        """Carga de datos desde la base de datos"""
        self.productos_inventario = self.obtener_productos()

    def conectar_impresora_async(self):
        """Conecta la impresora en segundo plano"""
        def conectar():
            try:
                if self.printer_manager.conectar_impresora():
                    self.impresora_conectada = True
                    print("✅ Impresora lista para usar")
                else:
                    print("⚠️ No se pudo conectar la impresora")
            except Exception as e:
                print(f"⚠️ Error conectando impresora: {e}")
        
        # Ejecutar en hilo separado para no bloquear la UI
        import threading
        thread = threading.Thread(target=conectar, daemon=True)
        thread.start()

    def crear_interfaz(self):
        """Construye toda la interfaz de usuario"""
        # Header
        header = tk.Frame(self.ventana, bg="#FF1493", height=80)
        header.grid(row=0, column=0, columnspan=6, sticky="ew", padx=5, pady=5)
        header.grid_propagate(False)
        tk.Label(header, text="💖 VARIEDADES MARCE 🌸", font=("Arial", 18, "bold"), 
                bg="#FF1493", fg="white").pack(pady=15)

        # Info factura
        self.crear_info_frame()
        
        # Inputs
        self.crear_input_frame()
        
        # Botones
        self.crear_botones()
        
        # Tabla
        self.crear_tabla()
        
        # Total
        self.crear_total_frame()
        
        # Botones de pago
        self.crear_botones_pago()

    def crear_info_frame(self):
        """Frame de información de factura"""
        info_frame = tk.Frame(self.ventana, bg="#FFB6C1")
        info_frame.grid(row=1, column=0, columnspan=6, sticky="ew", padx=10, pady=5)
        
        self.lbl_factura = tk.Label(info_frame, text=f"🧾 Factura: {self.factura_num}",
                                   font=("Arial", 10), bg="#FFB6C1", fg="#8B0054")
        self.lbl_factura.grid(row=0, column=0, padx=10)
        
        self.lbl_fecha = tk.Label(info_frame, text="", font=("Arial", 10), bg="#FFB6C1", fg="#8B0054")
        self.lbl_fecha.grid(row=0, column=1, padx=10)
        
        self.lbl_hora = tk.Label(info_frame, text="", font=("Arial", 10), bg="#FFB6C1", fg="#8B0054")
        self.lbl_hora.grid(row=0, column=2, padx=10)

    def crear_input_frame(self):
        """Frame de inputs principales"""
        input_frame = tk.Frame(self.ventana, bg="#FFC0CB", relief="raised", bd=2)
        input_frame.grid(row=2, column=0, columnspan=6, sticky="ew", padx=10, pady=10)

        tk.Label(input_frame, text="👤 Documento:", font=("Arial", 10, "bold"), 
                bg="#FFC0CB", fg="#8B0054").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.entry_doc = tk.Entry(input_frame, textvariable=self.documento, width=25, font=("Arial", 10))
        self.entry_doc.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(input_frame, text="🔢 Código:", font=("Arial", 10, "bold"), 
                bg="#FFC0CB", fg="#8B0054").grid(row=0, column=2, padx=10, pady=10)
        self.entry_codigo = tk.Entry(input_frame, textvariable=self.codigo_entrada, width=20, font=("Arial", 10))
        self.entry_codigo.grid(row=0, column=3, padx=10, pady=10)

    def crear_botones(self):
        """Crear botones principales"""
        button_frame = tk.Frame(self.ventana, bg="#FFB6C1")
        button_frame.grid(row=3, column=0, columnspan=6, pady=10)

        botones = [
            ("🔍 Buscar", self.buscar_producto, "#FF69B4"),
            ("📲 Escanear", self.escanear_codigo, "#FF69B4"),
            ("🗑️ Eliminar", self.eliminar_seleccionado, "#DC143C")
        ]

        for i, (texto, comando, color) in enumerate(botones):
            btn = tk.Button(button_frame, text=texto, command=comando, bg=color, fg="white",
                           font=("Arial", 10, "bold"), padx=15, pady=5)
            btn.grid(row=0, column=i, padx=10)

    def crear_tabla(self):
        """Crear tabla de productos"""
        tabla_frame = tk.Frame(self.ventana, bg="#FFB6C1")
        tabla_frame.grid(row=4, column=0, columnspan=6, padx=10, pady=10, sticky="ew")

        tk.Label(tabla_frame, text="🛍️ Productos en el carrito:", font=("Arial", 12, "bold"),
                bg="#FFB6C1", fg="#8B0054").pack(pady=5)

        self.tabla = ttk.Treeview(tabla_frame, columns=("Producto", "Precio", "Cantidad", "Total"), 
                                 show="headings", height=10)
        
        for col in ("Producto", "Precio", "Cantidad", "Total"):
            self.tabla.heading(col, text=col)
            self.tabla.column(col, width=200, anchor="center")
        
        self.tabla.pack(padx=10, pady=5)

    def crear_total_frame(self):
        """Frame del total"""
        total_frame = tk.Frame(self.ventana, bg="#FF1493", relief="raised", bd=3)
        total_frame.grid(row=5, column=0, columnspan=6, sticky="ew", padx=10, pady=10)

        tk.Label(total_frame, text="💸 TOTAL:", font=("Arial", 16, "bold"),
                bg="#FF1493", fg="white").pack(side="left", padx=20, pady=10)
        
        self.total_label = tk.Label(total_frame, text=self.formato_peso(0), font=("Arial", 18, "bold"),
                                   bg="#FF1493", fg="yellow")
        self.total_label.pack(side="right", padx=20, pady=10)

    def crear_botones_pago(self):
        """Botones de pago y nueva venta"""
        payment_frame = tk.Frame(self.ventana, bg="#FFB6C1")
        payment_frame.grid(row=6, column=0, columnspan=6, pady=20)
        
        tk.Button(payment_frame, text="💳 PROCESAR PAGO", command=self.pagar, bg="#32CD32", fg="white",
                 font=("Arial", 14, "bold"), padx=30, pady=15).pack()
        
        tk.Button(payment_frame, text="🆕 Nueva Venta", command=self.limpiar_formulario, bg="#FF8C00", fg="white",
                 font=("Arial", 10, "bold"), padx=20, pady=5).pack(pady=10)

    def configurar_eventos(self):
        """Configurar eventos de teclado y focus"""
        self.entry_codigo.bind('<Return>', lambda e: self.escanear_codigo())
        self.entry_codigo.bind('<KeyRelease>', self.on_codigo_change)
        self.entry_doc.focus()
        self.actualizar_hora()

    def on_codigo_change(self, event):
        """Detecta cuando se escanea un código de barras completo"""
        codigo = self.codigo_entrada.get().strip()
        
        # Si el código tiene más de 3 caracteres y termina con Enter, procesarlo automáticamente
        if len(codigo) >= 4 and event.keysym == 'Return':
            self.escanear_codigo()
        # Auto-escanear si se detecta un código largo (típico de scanners)
        elif len(codigo) >= 8:
            self.ventana.after(100, self.escanear_codigo)  # Pequeño delay para completar la entrada

    # ====================================================================================
    #   FUNCIONES DE DATOS Y UTILIDADES
    # ====================================================================================

    def obtener_productos(self):
        """Obtener productos del inventario"""
        ruta_db = os.path.join(os.path.dirname(__file__), '..', 'database', 'ventas.db')
        try:
            with sqlite3.connect(ruta_db) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT codigo, nombre, stock, precio FROM productos")
                return cursor.fetchall()
        except Exception as e:
            messagebox.showerror("Error DB", f"Error de base de datos: {e}")
            return []

    def formato_peso(self, valor):
        """Formato de pesos colombianos"""
        return f"${int(valor):,.0f} COP"

    def limpiar_precio(self, texto):
        """Convertir texto de precio a número"""
        return float(texto.replace("$", "").replace("COP", "").replace(",", "").strip() or 0)

    def actualizar_total(self):
        """Actualizar el display del total"""
        self.total_label.config(text=self.formato_peso(self.total_general.get()))

    def actualizar_hora(self):
        """Actualizar hora cada segundo"""
        ahora = datetime.now()
        self.lbl_fecha.config(text=f"📅 {ahora.strftime('%d-%m-%Y')}")
        self.lbl_hora.config(text=f"🕒 {ahora.strftime('%H:%M:%S')}")
        self.ventana.after(1000, self.actualizar_hora)

    def abrir_caja_registradora(self):
        """Abre la caja registradora enviando comando ESC/POS"""
        try:
            if self.printer_manager and self.printer_manager.printer:
                # Comando para abrir caja: ESC p m t1 t2
                self.printer_manager.printer._raw(b'\x1B\x70\x00\x19\x19')
                print("💰 Caja registradora abierta")
            else:
                print("⚠️ No se pudo abrir la caja - impresora no conectada")
        except Exception as e:
            print(f"⚠️ Error al abrir caja: {e}")

    # ====================================================================================
    #   FUNCIONES DE INTERFAZ
    # ====================================================================================

    def buscar_producto(self):
        """Ventana de búsqueda de productos"""
        ventana = tk.Toplevel(self.ventana)
        ventana.title("🔎 Buscar producto")
        ventana.geometry("700x500")
        ventana.configure(bg="#FFB6C1")
        ventana.grab_set()

        filtro = tk.StringVar()
        tk.Label(ventana, text="🔍 Buscar:", bg="#FFB6C1", fg="#8B0054", 
                font=("Arial", 12, "bold")).pack(pady=10)
        
        entry = tk.Entry(ventana, textvariable=filtro, width=50, font=("Arial", 10))
        entry.pack(pady=5)
        entry.focus()

        # Lista de productos
        lista = ttk.Treeview(ventana, columns=("Código", "Nombre", "Stock", "Precio"), 
                            show="headings", height=15)
        for col in ("Código", "Nombre", "Stock", "Precio"):
            lista.heading(col, text=col)
            lista.column(col, width=150, anchor="center")
        lista.pack(padx=10, pady=10)

        def actualizar_lista():
            lista.delete(*lista.get_children())
            filtro_texto = filtro.get().lower()
            
            for codigo, nombre, stock, precio in self.productos_inventario:
                if not filtro_texto or filtro_texto in f"{codigo} {nombre}".lower():
                    lista.insert("", tk.END, values=(codigo, nombre, stock, self.formato_peso(precio)))

        def seleccionar():
            item = lista.focus()
            if item:
                valores = lista.item(item)["values"]
                codigo = valores[0]
                nombre = valores[1] 
                stock = int(valores[2])
                precio = self.limpiar_precio(valores[3])
                
                print(f"DEBUG: Seleccionando - Código: {codigo}, Stock: {stock}")
                
                if stock > 0:
                    self.agregar_producto(codigo, nombre, precio)
                    ventana.destroy()
                else:
                    messagebox.showwarning("Sin stock", "Producto sin stock disponible")

        actualizar_lista()
        filtro.trace("w", lambda *args: actualizar_lista())
        
        tk.Button(ventana, text="✨ Seleccionar", command=seleccionar, bg="#FF69B4", fg="white",
                 font=("Arial", 10, "bold"), padx=20).pack(pady=10)
        
        ventana.bind('<Return>', lambda e: seleccionar())

    def agregar_producto(self, codigo, nombre, precio):
        """Agregar producto al carrito"""
        # Verificar stock disponible - buscar por código exacto o con formato
        stock_disponible = 0
        for p in self.productos_inventario:
            if str(p[0]) == str(codigo) or str(p[0]).zfill(5) == str(codigo).zfill(5):
                stock_disponible = p[2]
                break
        
        print(f"DEBUG: Código {codigo}, Stock disponible: {stock_disponible}")
        
        # Buscar si ya está en el carrito
        cantidad_actual = 0
        item_existente = None
        
        for item in self.tabla.get_children():
            valores = self.tabla.item(item)["values"]
            if len(valores) >= 5 and str(valores[4]) == str(codigo):
                cantidad_actual = int(valores[2])
                item_existente = item
                break

        # Verificar si se puede agregar una unidad más
        if cantidad_actual + 1 > stock_disponible:
            messagebox.showwarning("Stock insuficiente", 
                                 f"Stock disponible: {stock_disponible}\n" +
                                 f"Ya tienes {cantidad_actual} en el carrito")
            return

        if item_existente:
            # Actualizar cantidad existente
            nueva_cantidad = cantidad_actual + 1
            nuevo_total = precio * nueva_cantidad
            valores = list(self.tabla.item(item_existente)["values"])
            valores[2] = nueva_cantidad
            valores[3] = self.formato_peso(nuevo_total)
            self.tabla.item(item_existente, values=valores)
            self.total_general.set(self.total_general.get() + precio)
        else:
            # Verificar que hay stock para agregar el primer producto
            if stock_disponible <= 0:
                messagebox.showwarning("Sin stock", f"El producto '{nombre}' no tiene stock disponible")
                return
            
            # Agregar nuevo producto
            self.tabla.insert("", tk.END, values=(nombre, self.formato_peso(precio), 1, 
                                                 self.formato_peso(precio), codigo))
            self.total_general.set(self.total_general.get() + precio)
        
        self.actualizar_total()

    def escanear_codigo(self):
        """Procesar código escaneado o ingresado"""
        codigo = self.codigo_entrada.get().strip()
        if not codigo:
            return

        print(f"DEBUG: Buscando código: '{codigo}'")
        
        # Buscar producto - buscar tanto código exacto como con ceros
        producto = None
        for p in self.productos_inventario:
            if str(p[0]) == codigo or str(p[0]).zfill(5) == codigo:
                producto = p
                break
        
        if producto:
            print(f"DEBUG: Producto encontrado: {producto[1]}, Stock: {producto[2]}")
            
            if producto[2] > 0:  # Verificar stock
                self.agregar_producto(str(producto[0]), producto[1], producto[3])
                self.codigo_entrada.set("")
                self.entry_codigo.focus()
            else:
                messagebox.showwarning("Sin stock", f"'{producto[1]}' sin stock")
                self.codigo_entrada.set("")
        else:
            print(f"DEBUG: Producto no encontrado para código: '{codigo}'")
            print(f"DEBUG: Códigos disponibles en inventario: {[str(p[0]) for p in self.productos_inventario[:5]]}")
            messagebox.showerror("No encontrado", "Producto no existe")
            self.codigo_entrada.set("")

    def eliminar_seleccionado(self):
        """Eliminar producto seleccionado del carrito"""
        item = self.tabla.focus()
        if not item:
            messagebox.showwarning("Selección", "Selecciona un producto para eliminar")
            return
        
        valores = self.tabla.item(item)["values"]
        total_item = self.limpiar_precio(valores[3])
        self.total_general.set(self.total_general.get() - total_item)
        self.tabla.delete(item)
        self.actualizar_total()

    def pagar(self):
        """Procesar pago de la venta"""
        if not self.documento.get().strip():
            messagebox.showerror("Documento requerido", "Ingresa el documento del cliente")
            self.entry_doc.focus()
            return
        
        if self.total_general.get() <= 0:
            messagebox.showerror("Sin productos", "Agrega productos antes de pagar")
            return

        ventana = tk.Toplevel(self.ventana)
        ventana.title("💳 Procesar Pago")
        ventana.geometry("400x250")
        ventana.configure(bg="#FFB6C1")
        ventana.grab_set()

        # Centrar ventana
        ventana.update_idletasks()
        x = (self.ventana.winfo_screenwidth() // 2) - 200
        y = (self.ventana.winfo_screenheight() // 2) - 125
        ventana.geometry(f"400x250+{x}+{y}")

        tk.Label(ventana, text="💖 PROCESAR PAGO", font=("Arial", 16, "bold"),
                bg="#FFB6C1", fg="#8B0054").pack(pady=15)

        tk.Label(ventana, text="💸 Total:", font=("Arial", 12, "bold"),
                bg="#FFB6C1", fg="#8B0054").pack(pady=5)
        tk.Label(ventana, text=self.formato_peso(self.total_general.get()),
                font=("Arial", 14, "bold"), bg="#FFB6C1", fg="#FF1493").pack(pady=5)

        tk.Label(ventana, text="💵 Efectivo recibido:", font=("Arial", 12, "bold"),
                bg="#FFB6C1", fg="#8B0054").pack(pady=5)
        
        efectivo = tk.DoubleVar()
        entry = tk.Entry(ventana, textvariable=efectivo, font=("Arial", 12), width=20)
        entry.pack(pady=5)
        entry.focus()

        def completar():
            try:
                recibido = efectivo.get()
                total = self.total_general.get()
                
                if recibido < total:
                    messagebox.showwarning("Efectivo insuficiente", 
                                         f"Faltan: {self.formato_peso(total - recibido)}")
                    return

                # Procesar venta
                if self.procesar_venta_completa(recibido, total):
                    ventana.destroy()
                    
            except (tk.TclError, ValueError):
                messagebox.showerror("Error", "Ingresa un monto válido")

        entry.bind('<Return>', lambda e: completar())
        
        tk.Button(ventana, text="✅ Completar Pago", command=completar, bg="#32CD32", fg="white",
                 font=("Arial", 12, "bold"), padx=20, pady=10).pack(pady=20)

    def procesar_venta_completa(self, recibido, total):
        """Procesa toda la venta: DB + impresión + caja"""
        try:
            # Guardar en base de datos
            id_venta = self.guardar_venta_db(self.documento.get(), total)
            if not id_venta:
                return False

            # Preparar datos para impresión
            productos_venta = []
            productos_detalle = []
            
            for item in self.tabla.get_children():
                valores = self.tabla.item(item)["values"]
                if len(valores) >= 5:
                    nombre, precio_txt, cantidad, subtotal_txt, codigo = valores
                    precio = self.limpiar_precio(precio_txt)
                    subtotal = self.limpiar_precio(subtotal_txt)
                    
                    productos_venta.append((nombre, precio, int(cantidad)))
                    productos_detalle.append((codigo, nombre, precio, int(cantidad), subtotal))

            # Guardar detalles y actualizar stock
            if not self.guardar_detalle_ventas_db(id_venta, productos_detalle):
                return False

            # Mostrar resultado
            vuelto = recibido - total
            resultado = f"""💖 VENTA COMPLETADA 💖

🧾 Factura: {self.factura_num}
📅 {datetime.now().strftime('%d-%m-%Y')} 🕒 {datetime.now().strftime('%H:%M:%S')}
👤 Cliente: {self.documento.get()}

💸 Total: {self.formato_peso(total)}
💵 Recibido: {self.formato_peso(recibido)}
💰 Cambio: {self.formato_peso(vuelto)}

🌸 ¡Gracias por tu compra! 🌸"""
            
            messagebox.showinfo("✅ Pago Completado", resultado)

            # Imprimir factura
            self.imprimir_factura(productos_venta, total)
            
            # Abrir caja registradora
            self.abrir_caja_registradora()
            
            # Actualizar inventario y limpiar
            self.productos_inventario = self.obtener_productos()
            self.limpiar_formulario()
            
            return True
            
        except Exception as e:
            messagebox.showerror("Error", f"Error procesando venta: {e}")
            return False

    def imprimir_factura(self, productos, total):
        """Imprimir factura térmica"""
        if not IMPRESION_DISPONIBLE:
            messagebox.showinfo("Sin impresión", "Impresión no disponible")
            return

        try:
            # Reconectar impresora si es necesario
            if not self.impresora_conectada:
                if not self.printer_manager.conectar_impresora():
                    raise Exception("No se pudo conectar con la impresora")
                self.impresora_conectada = True

            # Datos de la factura - CAPTURAR INMEDIATAMENTE los datos actuales
            factura_data = {
                'factura': self.factura_num,
                'fecha': datetime.now().strftime('%d-%m-%Y'),
                'hora': datetime.now().strftime('%H:%M:%S'),
                'cliente': self.documento.get(),
                'productos': productos.copy(),  # Hacer copia de la lista
                'total': total
            }
            
            print(f"DEBUG: Imprimiendo factura {factura_data['factura']} para cliente {factura_data['cliente']}")
            print(f"DEBUG: Productos a imprimir: {len(factura_data['productos'])}")
            
            # Imprimir INMEDIATAMENTE
            self.printer_manager.imprimir_factura(factura_data)
            messagebox.showinfo("✅ Impresión", "¡Factura impresa exitosamente! 💖")
            
        except Exception as e:
            self.mostrar_error_impresion(e)

    def mostrar_error_impresion(self, error):
        """Mostrar ventana de error de impresión"""
        ventana = tk.Toplevel(self.ventana)
        ventana.title("❌ Error de impresión")
        ventana.geometry("500x300")
        ventana.configure(bg="#FFB6C1")
        ventana.grab_set()

        # Centrar ventana
        ventana.update_idletasks()
        x = (self.ventana.winfo_screenwidth() // 2) - 250
        y = (self.ventana.winfo_screenheight() // 2) - 150
        ventana.geometry(f"500x300+{x}+{y}")

        tk.Label(ventana, text="❌ ERROR DE IMPRESIÓN", font=("Arial", 14, "bold"),
                bg="#FFB6C1", fg="#8B0054").pack(pady=10)

        tk.Label(ventana, text="No se pudo imprimir la factura:", font=("Arial", 10),
                bg="#FFB6C1", fg="#8B0054").pack(pady=5)

        # Mostrar error
        error_frame = tk.Frame(ventana, bg="white", relief="sunken", bd=1)
        error_frame.pack(pady=10, padx=20, fill="x")
        tk.Label(error_frame, text=str(error), font=("Arial", 9), bg="white", fg="red",
                wraplength=450, justify="left").pack(pady=5, padx=5)

        tk.Label(ventana, text="💡 Soluciones:", font=("Arial", 10, "bold"),
                bg="#FFB6C1", fg="#8B0054").pack(pady=(10,5))

        soluciones = """• Verifica que la impresora esté encendida
• Revisa la conexión USB
• Reinicia la impresora
• Ejecuta la aplicación como administrador"""

        tk.Label(ventana, text=soluciones, font=("Arial", 9), bg="#FFB6C1", fg="#8B0054",
                justify="left").pack(pady=5)

        tk.Button(ventana, text="✅ Aceptar", command=ventana.destroy, bg="#FF69B4", fg="white",
                 font=("Arial", 10, "bold"), padx=20, pady=5).pack(pady=15)

    # ====================================================================================
    #   FUNCIONES DE BASE DE DATOS
    # ====================================================================================

    def guardar_venta_db(self, documento_cliente, total_venta):
        """Guardar venta principal en la base de datos"""
        ruta_db = os.path.join(os.path.dirname(__file__), '..', 'database', 'ventas.db')
        try:
            with sqlite3.connect(ruta_db) as conn:
                cursor = conn.cursor()
                fecha = datetime.now().strftime("%Y-%m-%d")
                hora = datetime.now().strftime("%H:%M:%S")

                cursor.execute(
                    "INSERT INTO ventas (fecha_venta, hora_venta, documento_cliente, total_venta) VALUES (?, ?, ?, ?)",
                    (fecha, hora, documento_cliente, total_venta)
                )
                
                id_venta = cursor.lastrowid
                conn.commit()
                return id_venta
                
        except Exception as e:
            messagebox.showerror("Error DB", f"Error guardando venta: {e}")
            return None

    def guardar_detalle_ventas_db(self, id_venta, productos_vendidos):
        """Guardar detalle de venta y actualizar stock"""
        ruta_db = os.path.join(os.path.dirname(__file__), '..', 'database', 'ventas.db')
        try:
            with sqlite3.connect(ruta_db) as conn:
                cursor = conn.cursor()
                
                for codigo, nombre, precio, cantidad, subtotal in productos_vendidos:
                    # Insertar detalle
                    cursor.execute(
                        "INSERT INTO detalle_ventas (id_venta, codigo_producto, nombre_producto, precio_unitario, cantidad, subtotal) VALUES (?, ?, ?, ?, ?, ?)", 
                        (id_venta, codigo, nombre, precio, cantidad, subtotal)
                    )
                    
                    # Actualizar stock
                    cursor.execute("SELECT stock FROM productos WHERE codigo = ?", (codigo,))
                    resultado = cursor.fetchone()
                    
                    if resultado:
                        nuevo_stock = resultado[0] - cantidad
                        cursor.execute("UPDATE productos SET stock = ? WHERE codigo = ?", (nuevo_stock, codigo))
                    else:
                        # Probar con código formateado
                        codigo_formateado = str(codigo).zfill(5)
                        cursor.execute("SELECT stock FROM productos WHERE codigo = ?", (codigo_formateado,))
                        resultado = cursor.fetchone()
                        
                        if resultado:
                            nuevo_stock = resultado[0] - cantidad
                            cursor.execute("UPDATE productos SET stock = ? WHERE codigo = ?", (nuevo_stock, codigo_formateado))

                conn.commit()
                return True
                
        except Exception as e:
            messagebox.showerror("Error DB", f"Error guardando detalle: {e}")
            return False

    def limpiar_formulario(self):
        """Limpiar formulario para nueva venta"""
        self.documento.set("")
        self.codigo_entrada.set("")
        self.total_general.set(0.0)
        self.factura_num = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Limpiar tabla
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        
        self.actualizar_total()
        self.lbl_factura.config(text=f"🧾 Factura: {self.factura_num}")
        self.entry_doc.focus()


# ====================================================================================
#   EJECUCIÓN PRINCIPAL
# ====================================================================================

if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    root.mainloop()