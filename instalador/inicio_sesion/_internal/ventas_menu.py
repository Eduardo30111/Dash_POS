# ====================================================================================
#   SISTEMA DE VENTAS - VARIEDADES MARCE - VERSIÓN MEJORADA Y CORREGIDA
# ====================================================================================

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import os
import threading

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
        self.ultima_factura = None  # Guardar última factura para reimpresión
    
    def conectar_impresora(self):
        """Conecta automáticamente usando el método que funcione"""
        # Configuraciones comunes de impresoras térmicas
        configs = [
            # DIG ISH58 / XP-58 - TU IMPRESORA ESPECÍFICA
            {"vid": 0x0fe6, "pid": 0x811e, "in_ep": 0x82, "out_ep": 0x01, "model": "DIG_ISH58"},
            {"vid": 0x0fe6, "pid": 0x811f, "in_ep": 0x82, "out_ep": 0x01, "model": "DIG_ISH58"}, 
            {"vid": 0x0fe6, "pid": 0x811d, "in_ep": 0x82, "out_ep": 0x01, "model": "DIG_ISH58"},
            # XP-58 genérico
            {"vid": 0x1fc9, "pid": 0x2016, "in_ep": 0x82, "out_ep": 0x01, "model": "XP58"},
            {"vid": 0x04b8, "pid": 0x0e28, "in_ep": 0x82, "out_ep": 0x01, "model": "XP58"},
            # DigitalPOS otros modelos
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
            
            # Detectar si es DIG ISH58/XP-58 para manejo especial
            if config.get("model") in ["DIG_ISH58", "XP58"] or config["vid"] == 0x0fe6:
                print(f"✅ Conexión USB exitosa - DIG ISH58/XP-58: {hex(config['vid'])}:{hex(config['pid'])}")
                self.is_dig_ish58 = True
            else:
                print(f"✅ Conexión USB exitosa: {hex(config['vid'])}:{hex(config['pid'])}")
                self.is_dig_ish58 = False
            
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
    
    def imprimir_factura(self, factura_data, callback=None):
        """Imprime la factura usando la conexión establecida - OPTIMIZADO PARA DIG ISH58/XP-58"""
        if not self.printer:
            raise Exception("No hay impresora conectada")
        
        def _imprimir():
            try:
                print(f"DEBUG PrinterManager: INICIANDO impresión FORZADA para DIG ISH58 - factura {factura_data['factura']}")
                
                # MÉTODO ESPECÍFICO PARA DIG ISH58/XP-58: DOBLE CONEXIÓN
                p = None
                
                try:
                    # PRIMERA CONEXIÓN: Preparar datos
                    if self.printer_type == "USB" and self.config_exitosa:
                        p = Usb(
                            idVendor=self.config_exitosa["vid"],
                            idProduct=self.config_exitosa["pid"],
                            timeout=5000,  # Timeout más largo para DIG ISH58
                            in_ep=self.config_exitosa["in_ep"],
                            out_ep=self.config_exitosa["out_ep"]
                        )
                    else:
                        p = self.printer
                    
                    # RESET COMPLETO ESPECÍFICO PARA XP-58
                    print("DEBUG: Aplicando reset específico XP-58...")
                    p._raw(b'\x1B\x40')  # ESC @ - Reset completo
                    p._raw(b'\x1B\x4A\x00')  # ESC J - Feed 0 líneas (flush buffer)
                    p._raw(b'\x0C')  # Form feed - limpiar buffer
                    
                    # ESPERAR UN MOMENTO PARA QUE PROCESE EL RESET
                    import time
                    time.sleep(0.1)
                    
                    # CONSTRUIR TODA LA FACTURA EN MEMORIA PRIMERO
                    factura_completa = ""
                    
                    # Header
                    factura_completa += "        VARIEDADES MARCE\n"
                    factura_completa += "    Centro de copiado y belleza\n"
                    factura_completa += "       Cel: 300-123-4567\n"
                    factura_completa += "=" * 32 + "\n"
                    
                    # Información de venta
                    factura_completa += f"Factura: {factura_data['factura']}\n"
                    factura_completa += f"Fecha: {factura_data['fecha']}\n"
                    factura_completa += f"Hora: {factura_data['hora']}\n"
                    factura_completa += f"Cliente: {factura_data['cliente']}\n"
                    factura_completa += "-" * 32 + "\n"
                    
                    factura_completa += "Producto           Cant  Precio\n"
                    factura_completa += "-" * 32 + "\n"
                    
                    # Productos
                    total_items = 0
                    for nombre, precio, cantidad in factura_data['productos']:
                        subtotal = precio * cantidad
                        total_items += cantidad
                        nombre_corto = nombre[:15].ljust(15)
                        factura_completa += f"{nombre_corto} {cantidad:>2}x ${precio:>6,.0f}\n"
                        if cantidad > 1:
                            factura_completa += f"      Subtotal: ${subtotal:>8,.0f}\n"
                    
                    # Total
                    factura_completa += "-" * 32 + "\n"
                    factura_completa += f"Total Items: {total_items}\n"
                    factura_completa += f"TOTAL: ${factura_data['total']:>16,.0f}\n"
                    factura_completa += "=" * 32 + "\n"
                    
                    # Footer
                    factura_completa += "     Gracias por tu compra!\n"
                    factura_completa += "        Vuelve pronto\n"
                    factura_completa += "\n\n\n"
                    
                    # ENVIAR TODO DE UNA VEZ - MÉTODO XP-58
                    print("DEBUG: Enviando factura completa...")
                    p._raw(factura_completa.encode('cp437', errors='ignore'))
                    
                    # FORZAR CORTE MÚLTIPLE PARA XP-58
                    print("DEBUG: Aplicando cortes múltiples...")
                    p._raw(b'\x1D\x56\x41\x03')  # Corte completo con feed
                    p._raw(b'\x1D\x56\x00')      # Corte completo alternativo
                    p._raw(b'\x0A\x0A\x0A')      # Feeds adicionales
                    
                    # FLUSH FORZADO ESPECÍFICO PARA DIG ISH58
                    print("DEBUG: Aplicando flush forzado...")
                    try:
                        if hasattr(p, '_device'):
                            # Método 1: Flush directo del device
                            p._device.write(p._out_ep, b'\x00', timeout=1000)
                        elif hasattr(p, 'device'):
                            # Método 2: Write vacío para flush
                            p.device.write(p.out_ep, b'\x00', timeout=1000)
                    except:
                        pass
                    
                    # CERRAR Y REABRIR CONEXIÓN PARA FORZAR FLUSH (ESPECÍFICO XP-58)
                    print("DEBUG: Forzando flush con reconexión...")
                    try:
                        p.close()
                    except:
                        pass
                    
                    time.sleep(0.2)
                    
                    # SEGUNDA CONEXIÓN: Verificar que se envió
                    try:
                        p2 = Usb(
                            idVendor=self.config_exitosa["vid"],
                            idProduct=self.config_exitosa["pid"],
                            timeout=2000,
                            in_ep=self.config_exitosa["in_ep"],
                            out_ep=self.config_exitosa["out_ep"]
                        )
                        # Enviar comando final de confirmación
                        p2._raw(b'\x1B\x4A\x01')  # Feed final para asegurar procesamiento
                        p2.close()
                    except:
                        pass  # No importa si falla la segunda conexión
                    
                except Exception as e:
                    print(f"DEBUG: Error en primera fase: {e}")
                    # MÉTODO FALLBACK: Usar conexión original con flush múltiple
                    p = self.printer
                    p._raw(factura_completa.encode('cp437', errors='ignore'))
                    p._raw(b'\x1D\x56\x00')
                    p._raw(b'\x0A\x0A')
                
                # GUARDAR PARA REIMPRESIÓN
                self.ultima_factura = factura_data.copy()
                
                print(f"DEBUG PrinterManager: ✅ Factura {factura_data['factura']} ENVIADA CON FLUSH FORZADO")
                
                if callback:
                    callback(True, "Factura impresa con flush forzado")
                
                return True
                
            except Exception as e:
                error_msg = f"Error al imprimir: {str(e)}"
                print(f"DEBUG PrinterManager: ❌ {error_msg}")
                if callback:
                    callback(False, error_msg)
                raise Exception(error_msg)
        
        # EJECUTAR INMEDIATAMENTE - SIN THREADING PARA FORZAR SINCRONÍA
        _imprimir()
    
    def reimprimir_ultima_factura(self):
        """Reimprime la última factura guardada"""
        if not self.ultima_factura:
            raise Exception("No hay factura previa para reimprimir")
        
        print("🔄 Reimprimiendo última factura...")
        self.imprimir_factura(self.ultima_factura)
    
    def abrir_caja_registradora(self):
        """Abre la caja registradora enviando comando ESC/POS - OPTIMIZADO PARA DIG ISH58"""
        try:
            if self.printer:
                print("DEBUG: Enviando comando de apertura de caja para DIG ISH58...")
                
                # MÉTODO ESPECÍFICO PARA DIG ISH58/XP-58: Múltiples comandos
                comandos_caja = [
                    b'\x1B\x70\x00\x32\x32',  # ESC p 0 50 50 - Comando principal
                    b'\x1B\x70\x01\x32\x32',  # ESC p 1 50 50 - Puerto alternativo
                    b'\x1C\x70\x00\x7F\xFF', # Comando alternativo DIG
                    b'\x10\x14\x01\x00\x05', # Comando específico XP-58
                ]
                
                for i, comando in enumerate(comandos_caja):
                    try:
                        print(f"DEBUG: Enviando comando caja #{i+1}...")
                        self.printer._raw(comando)
                        
                        # Pequeña pausa entre comandos
                        import time
                        time.sleep(0.1)
                        
                    except Exception as e:
                        print(f"DEBUG: Comando #{i+1} falló: {e}")
                        continue
                
                # FLUSH FORZADO igual que en impresión
                try:
                    if hasattr(self.printer, '_device'):
                        self.printer._device.write(self.printer._out_ep, b'\x00', timeout=1000)
                except:
                    pass
                
                print("💰 Comandos de caja enviados - DIG ISH58")
                return True
            else:
                raise Exception("Impresora no conectada")
        except Exception as e:
            print(f"⚠️ Error al abrir caja: {e}")
            raise e

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
        self.ventana.geometry("850x750")  # Aumentado para botones de emergencia
        self.ventana.configure(bg="#FFB6C1")
        
        # Centrar ventana
        self.ventana.update_idletasks()
        width, height = 850, 750
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
            'Emergency.TButton': {'background': '#FF4500', 'foreground': 'white', 'font': ('Arial', 9, 'bold')},
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
        
        # Botones principales
        self.crear_botones()
        
        # BOTONES DE EMERGENCIA - NUEVA SECCIÓN
        self.crear_botones_emergencia()
        
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

    def crear_botones_emergencia(self):
        """NUEVA FUNCIÓN - Crear botones de emergencia"""
        emergency_frame = tk.Frame(self.ventana, bg="#FFE4E1", relief="raised", bd=2)
        emergency_frame.grid(row=4, column=0, columnspan=6, sticky="ew", padx=10, pady=5)
        
        tk.Label(emergency_frame, text="🚨 BOTONES DE EMERGENCIA 🚨", font=("Arial", 10, "bold"),
                bg="#FFE4E1", fg="#8B0000").pack(pady=5)
        
        btn_frame = tk.Frame(emergency_frame, bg="#FFE4E1")
        btn_frame.pack(pady=5)
        
        # Botón abrir caja
        btn_abrir_caja = tk.Button(btn_frame, text="💰 ABRIR CAJA", command=self.emergencia_abrir_caja,
                                  bg="#FF4500", fg="white", font=("Arial", 9, "bold"), padx=15, pady=5)
        btn_abrir_caja.pack(side="left", padx=10)
        
        # Botón reimprimir factura
        btn_reimprimir = tk.Button(btn_frame, text="🖨️ REIMPRIMIR", command=self.emergencia_reimprimir,
                                  bg="#FF6347", fg="white", font=("Arial", 9, "bold"), padx=15, pady=5)
        btn_reimprimir.pack(side="left", padx=10)

    def crear_tabla(self):
        """Crear tabla de productos"""
        tabla_frame = tk.Frame(self.ventana, bg="#FFB6C1")
        tabla_frame.grid(row=5, column=0, columnspan=6, padx=10, pady=10, sticky="ew")

        tk.Label(tabla_frame, text="🛍️ Productos en el carrito:", font=("Arial", 12, "bold"),
                bg="#FFB6C1", fg="#8B0054").pack(pady=5)

        self.tabla = ttk.Treeview(tabla_frame, columns=("Producto", "Precio", "Cantidad", "Total"), 
                                 show="headings", height=8)  # Reducido para espacio de botones
        
        for col in ("Producto", "Precio", "Cantidad", "Total"):
            self.tabla.heading(col, text=col)
            self.tabla.column(col, width=200, anchor="center")
        
        self.tabla.pack(padx=10, pady=5)

    def crear_total_frame(self):
        """Frame del total"""
        total_frame = tk.Frame(self.ventana, bg="#FF1493", relief="raised", bd=3)
        total_frame.grid(row=6, column=0, columnspan=6, sticky="ew", padx=10, pady=10)

        tk.Label(total_frame, text="💸 TOTAL:", font=("Arial", 16, "bold"),
                bg="#FF1493", fg="white").pack(side="left", padx=20, pady=10)
        
        self.total_label = tk.Label(total_frame, text=self.formato_peso(0), font=("Arial", 18, "bold"),
                                   bg="#FF1493", fg="yellow")
        self.total_label.pack(side="right", padx=20, pady=10)

    def crear_botones_pago(self):
        """Botones de pago y nueva venta"""
        payment_frame = tk.Frame(self.ventana, bg="#FFB6C1")
        payment_frame.grid(row=7, column=0, columnspan=6, pady=15)
        
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
        """Detecta cuando se escanea un código de barras completo - MEJORADO"""
        codigo = self.codigo_entrada.get().strip()
        
        # Si se presiona Enter, procesar inmediatamente
        if event.keysym == 'Return' and len(codigo) >= 1:
            self.escanear_codigo()
            return
        
        # Auto-escanear si se detecta un código largo (típico de scanners)
        if len(codigo) >= 8:
            # Cancelar cualquier timer anterior
            if hasattr(self, '_scan_timer'):
                self.ventana.after_cancel(self._scan_timer)
            
            # Programar escaneo automático con delay mínimo
            self._scan_timer = self.ventana.after(50, self.escanear_codigo)

    # ====================================================================================
    #   FUNCIONES DE EMERGENCIA - NUEVAS
    # ====================================================================================
    
    def emergencia_abrir_caja(self):
        """Función de emergencia para abrir caja registradora - CORREGIDA"""
        try:
            print("DEBUG: Botón ABRIR CAJA presionado")
            
            if not self.printer_manager:
                messagebox.showerror("Error", "Sistema de impresión no disponible")
                return
            
            # FORZAR RECONEXIÓN SI ES NECESARIO
            if not self.impresora_conectada:
                print("DEBUG: Reconectando impresora...")
                messagebox.showwarning("Impresora", "Intentando conectar impresora...")
                if not self.printer_manager.conectar_impresora():
                    messagebox.showerror("Error", "No se pudo conectar con la impresora")
                    return
                self.impresora_conectada = True
            
            # INTENTAR ABRIR CAJA CON MANEJO DE ERRORES DETALLADO
            print("DEBUG: Ejecutando comando abrir caja...")
            resultado = self.printer_manager.abrir_caja_registradora()
            
            if resultado:
                print("DEBUG: ✅ Comando enviado exitosamente")
                messagebox.showinfo("✅ Caja Abierta", "💰 Caja registradora abierta exitosamente")
            else:
                print("DEBUG: ❌ Comando falló sin excepción")
                messagebox.showwarning("Advertencia", "Comando enviado pero la caja no respondió.\nVerifica la conexión de la caja.")
            
        except Exception as e:
            error_detallado = str(e)
            print(f"DEBUG: ❌ Error detallado: {error_detallado}")
            
            # MOSTRAR ERROR ESPECÍFICO Y OPCIONES
            error_window = tk.Toplevel(self.ventana)
            error_window.title("❌ Error Apertura Caja")
            error_window.geometry("500x300")
            error_window.configure(bg="#FFB6C1")
            error_window.grab_set()
            
            # Centrar ventana
            x = (self.ventana.winfo_screenwidth() // 2) - 250
            y = (self.ventana.winfo_screenheight() // 2) - 150
            error_window.geometry(f"500x300+{x}+{y}")
            
            tk.Label(error_window, text="❌ ERROR AL ABRIR CAJA", font=("Arial", 14, "bold"),
                    bg="#FFB6C1", fg="#8B0054").pack(pady=10)
            
            tk.Label(error_window, text=f"Error: {error_detallado}", font=("Arial", 10),
                    bg="#FFB6C1", fg="#8B0054", wraplength=450).pack(pady=5)
            
            tk.Label(error_window, text="🔧 Posibles soluciones:", font=("Arial", 10, "bold"),
                    bg="#FFB6C1", fg="#8B0054").pack(pady=(15,5))
            
            soluciones = """• Verifica que la caja esté conectada al puerto de la impresora
• Revisa que el cable de la caja esté bien conectado
• La caja debe estar conectada al puerto RJ11/RJ12 de la impresora
• Algunos modelos requieren configuración específica
• Prueba reiniciar la impresora"""
            
            tk.Label(error_window, text=soluciones, font=("Arial", 9),
                    bg="#FFB6C1", fg="#8B0054", justify="left").pack(pady=5)
            
            def reintentar_caja():
                error_window.destroy()
                print("DEBUG: Reintentando apertura de caja...")
                try:
                    # FORZAR NUEVA CONEXIÓN
                    self.impresora_conectada = False
                    self.emergencia_abrir_caja()
                except Exception as retry_error:
                    messagebox.showerror("Error", f"Reintento falló: {retry_error}")
            
            btn_frame = tk.Frame(error_window, bg="#FFB6C1")
            btn_frame.pack(pady=15)
            
            tk.Button(btn_frame, text="🔄 Reintentar", command=reintentar_caja,
                     bg="#FF8C00", fg="white", font=("Arial", 10, "bold"), padx=15).pack(side="left", padx=5)
            
            tk.Button(btn_frame, text="✅ Cerrar", command=error_window.destroy,
                     bg="#FF69B4", fg="white", font=("Arial", 10, "bold"), padx=15).pack(side="left", padx=5)
    
    def emergencia_reimprimir(self):
        """Función de emergencia para reimprimir última factura"""
        try:
            if not self.printer_manager:
                messagebox.showerror("Error", "Sistema de impresión no disponible")
                return
            
            if not self.printer_manager.ultima_factura:
                messagebox.showwarning("Sin factura", "No hay factura previa para reimprimir")
                return
            
            if not self.impresora_conectada:
                messagebox.showwarning("Impresora", "Intentando conectar impresora...")
                if not self.printer_manager.conectar_impresora():
                    messagebox.showerror("Error", "No se pudo conectar con la impresora")
                    return
                self.impresora_conectada = True
            
            # Mostrar confirmación con datos de la factura
            factura = self.printer_manager.ultima_factura
            confirmacion = f"""¿Reimprimir esta factura?

🧾 Factura: {factura['factura']}
📅 Fecha: {factura['fecha']} {factura['hora']}
👤 Cliente: {factura['cliente']}
💸 Total: ${factura['total']:,.0f}"""
            
            if messagebox.askyesno("Confirmar Reimpresión", confirmacion):
                def callback_reimprimir(exito, mensaje):
                    if exito:
                        self.ventana.after(0, lambda: messagebox.showinfo("✅ Reimpresión", "Factura reimpresa correctamente 🖨️"))
                    else:
                        self.ventana.after(0, lambda: messagebox.showerror("Error Reimpresión", f"Error: {mensaje}"))
                
                self.printer_manager.imprimir_factura(factura, callback_reimprimir)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo reimprimir:\n{str(e)}")

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

    # ====================================================================================
    #   FUNCIONES DE INTERFAZ - MEJORADAS
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
        """Agregar producto al carrito - CORREGIDO PARA SUMAR CANTIDADES"""
        # Verificar stock disponible - buscar por código exacto o con formato
        stock_disponible = 0
        for p in self.productos_inventario:
            if str(p[0]) == str(codigo) or str(p[0]).zfill(5) == str(codigo).zfill(5):
                stock_disponible = p[2]
                break
        
        print(f"DEBUG: Código {codigo}, Stock disponible: {stock_disponible}")
        
        # BUSCAR SI YA EXISTE EN EL CARRITO - MEJORADO
        cantidad_actual = 0
        item_existente = None
        
        for item in self.tabla.get_children():
            valores = self.tabla.item(item)["values"]
            if len(valores) >= 4:
                # Buscar por nombre del producto para mayor compatibilidad
                if str(valores[0]).strip().lower() == str(nombre).strip().lower():
                    cantidad_actual = int(valores[2])
                    item_existente = item
                    print(f"DEBUG: Producto encontrado en carrito - Cantidad actual: {cantidad_actual}")
                    break

        # Verificar si se puede agregar una unidad más
        if cantidad_actual + 1 > stock_disponible:
            messagebox.showwarning("Stock insuficiente", 
                                 f"Stock disponible: {stock_disponible}\n" +
                                 f"Ya tienes {cantidad_actual} en el carrito")
            return

        if item_existente:
            # ACTUALIZAR CANTIDAD EXISTENTE - ESTE ES EL FIX PRINCIPAL
            nueva_cantidad = cantidad_actual + 1
            nuevo_total = precio * nueva_cantidad
            
            # Actualizar la fila existente
            self.tabla.item(item_existente, values=(
                nombre, 
                self.formato_peso(precio), 
                nueva_cantidad, 
                self.formato_peso(nuevo_total)
            ))
            
            # Sumar solo el precio unitario al total general
            self.total_general.set(self.total_general.get() + precio)
            
            print(f"DEBUG: Producto actualizado - Nueva cantidad: {nueva_cantidad}, Nuevo total item: {nuevo_total}")
        else:
            # Verificar que hay stock para agregar el primer producto
            if stock_disponible <= 0:
                messagebox.showwarning("Sin stock", f"El producto '{nombre}' no tiene stock disponible")
                return
            
            # Agregar nuevo producto
            self.tabla.insert("", tk.END, values=(nombre, self.formato_peso(precio), 1, 
                                                 self.formato_peso(precio)))
            self.total_general.set(self.total_general.get() + precio)
            
            print(f"DEBUG: Nuevo producto agregado: {nombre}")
        
        self.actualizar_total()

    def escanear_codigo(self):
        """Procesar código escaneado o ingresado - MEJORADO"""
        codigo = self.codigo_entrada.get().strip()
        if not codigo:
            return

        print(f"DEBUG: Buscando código: '{codigo}'")
        
        # Buscar producto - buscar tanto código exacto como con ceros
        producto = None
        for p in self.productos_inventario:
            if str(p[0]) == codigo or str(p[0]).zfill(5) == codigo or codigo.zfill(5) == str(p[0]):
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
        """Procesa toda la venta: DB + impresión + caja - MEJORADO PARA IMPRESIÓN INMEDIATA"""
        try:
            print(f"DEBUG: Iniciando procesamiento de venta - Total: {total}")
            
            # CAPTURAR DATOS INMEDIATAMENTE ANTES DE CUALQUIER MODIFICACIÓN
            datos_venta_inmediatos = {
                'factura': self.factura_num,
                'fecha': datetime.now().strftime('%d-%m-%Y'),
                'hora': datetime.now().strftime('%H:%M:%S'),
                'cliente': self.documento.get(),
                'productos': [],
                'total': total
            }
            
            # CAPTURAR PRODUCTOS DEL CARRITO INMEDIATAMENTE
            productos_detalle = []
            for item in self.tabla.get_children():
                valores = self.tabla.item(item)["values"]
                if len(valores) >= 4:
                    nombre = str(valores[0])
                    precio_txt = str(valores[1])
                    cantidad = int(valores[2])
                    subtotal_txt = str(valores[3])
                    
                    precio = self.limpiar_precio(precio_txt)
                    subtotal = self.limpiar_precio(subtotal_txt)
                    
                    # Para impresión
                    datos_venta_inmediatos['productos'].append((nombre, precio, cantidad))
                    
                    # Para base de datos - buscar código del producto
                    codigo = None
                    for p in self.productos_inventario:
                        if str(p[1]).strip().lower() == nombre.strip().lower():
                            codigo = str(p[0])
                            break
                    
                    if codigo:
                        productos_detalle.append((codigo, nombre, precio, cantidad, subtotal))
            
            print(f"DEBUG: Datos capturados - {len(datos_venta_inmediatos['productos'])} productos")
            
            # Guardar en base de datos
            id_venta = self.guardar_venta_db(self.documento.get(), total)
            if not id_venta:
                return False

            # Guardar detalles y actualizar stock
            if not self.guardar_detalle_ventas_db(id_venta, productos_detalle):
                return False

            # IMPRIMIR INMEDIATAMENTE CON CALLBACK
            def callback_impresion(exito, mensaje):
                if exito:
                    print("DEBUG: ✅ Impresión completada exitosamente")
                    # Abrir caja registradora después de impresión exitosa
                    try:
                        self.printer_manager.abrir_caja_registradora()
                    except:
                        pass  # No fallar si no se puede abrir la caja
                else:
                    print(f"DEBUG: ❌ Error en impresión: {mensaje}")
                    # Mostrar error pero no detener el proceso
                    self.ventana.after(0, lambda: self.mostrar_error_impresion(Exception(mensaje)))

            # EJECUTAR IMPRESIÓN INMEDIATAMENTE
            if IMPRESION_DISPONIBLE and self.printer_manager:
                if not self.impresora_conectada:
                    if self.printer_manager.conectar_impresora():
                        self.impresora_conectada = True
                
                if self.impresora_conectada:
                    print("DEBUG: Enviando a impresión...")
                    self.printer_manager.imprimir_factura(datos_venta_inmediatos, callback_impresion)
                else:
                    print("DEBUG: No se pudo conectar impresora")

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

            # Actualizar inventario y limpiar DESPUÉS de mostrar el mensaje
            self.productos_inventario = self.obtener_productos()
            self.limpiar_formulario()
            
            return True
            
        except Exception as e:
            print(f"DEBUG: Error procesando venta: {e}")
            messagebox.showerror("Error", f"Error procesando venta: {e}")
            return False

    def mostrar_error_impresion(self, error):
        """Mostrar ventana de error de impresión - MEJORADO"""
        ventana = tk.Toplevel(self.ventana)
        ventana.title("❌ Error de impresión")
        ventana.geometry("500x350")
        ventana.configure(bg="#FFB6C1")
        ventana.grab_set()

        # Centrar ventana
        ventana.update_idletasks()
        x = (self.ventana.winfo_screenwidth() // 2) - 250
        y = (self.ventana.winfo_screenheight() // 2) - 175
        ventana.geometry(f"500x350+{x}+{y}")

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
• Ejecuta la aplicación como administrador
• Usa el botón 'REIMPRIMIR' en emergencias"""

        tk.Label(ventana, text=soluciones, font=("Arial", 9), bg="#FFB6C1", fg="#8B0054",
                justify="left").pack(pady=5)

        # Botón para reintentar impresión
        def reintentar():
            try:
                if self.printer_manager and self.printer_manager.ultima_factura:
                    self.printer_manager.imprimir_factura(self.printer_manager.ultima_factura)
                    ventana.destroy()
                    messagebox.showinfo("✅ Reintento", "Factura enviada nuevamente a impresión")
                else:
                    messagebox.showwarning("Sin datos", "No hay datos de factura para reintentar")
            except Exception as e:
                messagebox.showerror("Error", f"Error al reintentar: {e}")

        btn_frame = tk.Frame(ventana, bg="#FFB6C1")
        btn_frame.pack(pady=15)
        
        tk.Button(btn_frame, text="🔄 Reintentar", command=reintentar, bg="#FF8C00", fg="white",
                 font=("Arial", 10, "bold"), padx=15, pady=5).pack(side="left", padx=5)
        
        tk.Button(btn_frame, text="✅ Aceptar", command=ventana.destroy, bg="#FF69B4", fg="white",
                 font=("Arial", 10, "bold"), padx=20, pady=5).pack(side="left", padx=5)

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
                        print(f"DEBUG: Stock actualizado para {codigo}: {resultado[0]} -> {nuevo_stock}")
                    else:
                        # Probar con código formateado
                        codigo_formateado = str(codigo).zfill(5)
                        cursor.execute("SELECT stock FROM productos WHERE codigo = ?", (codigo_formateado,))
                        resultado = cursor.fetchone()
                        
                        if resultado:
                            nuevo_stock = resultado[0] - cantidad
                            cursor.execute("UPDATE productos SET stock = ? WHERE codigo = ?", (nuevo_stock, codigo_formateado))
                            print(f"DEBUG: Stock actualizado para {codigo_formateado}: {resultado[0]} -> {nuevo_stock}")

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
        
        print("DEBUG: Formulario limpiado para nueva venta")


# ====================================================================================
#   EJECUCIÓN PRINCIPAL
# ====================================================================================

if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    root.mainloop()