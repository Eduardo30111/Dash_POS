
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, date
import os
import threading

from paths import ventas_db_path
from layout_responsive import (
    bind_reflow_grid_uniform,
    bind_reflow_pack,
    centrar_ventana,
    modulo_scroll_finalizar,
)
from ui_theme import T, F_BODY, F_BODY_B, F_SMALL, F_SUB, FONT, style_ttk_pos_carrito_treeview, style_ttk_treeview_pos
from fiado_db import ensure_fiado_schema, upsert_cliente_por_cedula

_MESES = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)
_DIAS_SEMANA = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")


def _ventas_column_set(conn):
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ventas'")
    if not c.fetchone():
        return None
    c.execute("PRAGMA table_info(ventas)")
    return {row[1] for row in c.fetchall()}


def _detalle_ventas_column_set(conn):
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='detalle_ventas'")
    if not c.fetchone():
        return set()
    c.execute("PRAGMA table_info(detalle_ventas)")
    return {row[1] for row in c.fetchall()}


def _ventas_select_rows(conn, filtro_doc):
    """
    Filas (id_venta, fecha_venta, hora_venta, documento_cliente, total_venta, tipo_pago).
    id_venta usa id o rowid si la tabla no tiene columna id.
    """
    names = _ventas_column_set(conn)
    if not names:
        return [], "No existe la tabla ventas en la base de datos."
    id_expr = "id" if "id" in names else "rowid"
    if "fecha_venta" in names:
        fe = "fecha_venta"
    elif "fecha" in names:
        fe = "fecha"
    else:
        return [], "La tabla ventas no tiene columna de fecha (fecha_venta o fecha)."
    he = "hora_venta" if "hora_venta" in names else ("hora" if "hora" in names else "''")
    if "documento_cliente" in names:
        dc = "documento_cliente"
    elif "cedula" in names:
        dc = "cedula"
    else:
        dc = "''"
    if "total_venta" in names and "total" in names:
        tot = "COALESCE(total_venta, total, 0)"
    elif "total_venta" in names:
        tot = "total_venta"
    elif "total" in names:
        tot = "total"
    else:
        tot = "0"
    if "tipo_pago" in names:
        tip = "COALESCE(LOWER(tipo_pago), 'contado')"
    elif "metodo_pago" in names:
        tip = "COALESCE(LOWER(metodo_pago), 'contado')"
    else:
        tip = "'contado'"

    sql = (
        f"SELECT {id_expr} AS id_venta, {fe} AS fecha_venta, {he} AS hora_venta, "
        f"{dc} AS documento_cliente, {tot} AS total_venta, {tip} AS tipo_pago FROM ventas"
    )
    f = (filtro_doc or "").strip()
    args = []
    wh = []
    if f and "documento_cliente" in names:
        wh.append("documento_cliente LIKE ?")
        args.append(f"%{f}%")
    elif f and "cedula" in names:
        wh.append("cedula LIKE ?")
        args.append(f"%{f}%")
    if wh:
        sql += " WHERE " + " AND ".join(wh)
    sql += f" ORDER BY {fe} DESC, {he} DESC, {id_expr} DESC"
    c = conn.cursor()
    c.execute(sql, args)
    rows = [tuple(r) for r in c.fetchall()]
    if f and not wh:
        fl = f.lower()
        rows = [r for r in rows if fl in (str(r[3] or "")).lower()]
    return rows, None


def _venta_fecha_a_ymd(val):
    """Convierte el valor de fecha de una venta a 'YYYY-MM-DD' o None."""
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s[:10], fmt).date().strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _ventas_enriquecer_nombres(conn, filas6):
    """
    Añade columna nombre (cliente o primer producto del detalle).
    Cada fila: (id_venta, fecha, hora, doc, total, tipo, nombre).
    """
    if not filas6:
        return []
    names = _ventas_column_set(conn) or set()
    id_expr = "id" if "id" in names else "rowid"
    ids = [r[0] for r in filas6]
    c = conn.cursor()
    dnom = {}
    if "nombre" in names and ids:
        ph = ",".join("?" * len(ids))
        c.execute(f"SELECT {id_expr}, nombre FROM ventas WHERE {id_expr} IN ({ph})", ids)
        for a, b in c.fetchall():
            t = (b or "").strip()
            dnom[a] = t or None
    dprod = {}
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='detalle_ventas'")
    if c.fetchone() and ids:
        dcols = _detalle_ventas_column_set(conn)
        ord_col = "id" if dcols and "id" in dcols else "rowid"
        ph = ",".join("?" * len(ids))
        c.execute(
            f"SELECT id_venta, nombre_producto, {ord_col} AS _o FROM detalle_ventas WHERE id_venta IN ({ph}) "
            f"ORDER BY id_venta, {ord_col}",
            ids,
        )
        for idv, nom, _did in c.fetchall():
            if idv not in dprod and (nom or "").strip():
                nm = (nom or "").strip()
                dprod[idv] = (nm[:47] + "…") if len(nm) > 50 else nm
    out = []
    for r in filas6:
        i = r[0]
        n = dnom.get(i) or dprod.get(i) or "—"
        out.append((*r, n))
    return out


def _etiqueta_dia_combo(ymd):
    d = datetime.strptime(ymd, "%Y-%m-%d").date()
    suf = "  (hoy)" if d == date.today() else ""
    return f"{_DIAS_SEMANA[d.weekday()]} {d.day} de {_MESES[d.month - 1]} {d.year}{suf}"

# Configuración de impresión - CON MANEJO MEJORADO DE ERRORES
IMPRESION_DISPONIBLE = False
try:
    from escpos.printer import Usb
    import usb.core
    import usb.util
    
    # Intentar importar win32print pero con manejo de error separado
    try:
        import win32print
        from escpos.printer import Win32Raw
        WIN32_DISPONIBLE = True
    except ImportError:
        print("⚠️ Advertencia: pywin32 no está instalado. Impresión Windows no disponible.")
        WIN32_DISPONIBLE = False
        # Crear clase dummy para Win32Raw
        class Win32Raw:
            def __init__(self, *args, **kwargs):
                raise ImportError("pywin32 no instalado")
        
    IMPRESION_DISPONIBLE = True
    print("✅ Módulos de impresión cargados correctamente")
    
except ImportError as e:
    print(f"⚠️ Advertencia: Bibliotecas de impresión no disponibles. Error: {e}")
    # Crear clases dummy para que el código no falle
    class Usb:
        def __init__(self, *args, **kwargs):
            raise ImportError("Biblioteca python-escpos no instalada")
    class Win32Raw:
        def __init__(self, *args, **kwargs):
            raise ImportError("Biblioteca python-escpos no instalada")
    
    # Módulos dummy
    usb = type('usb', (), {'core': type('core', (), {'find': lambda *args: []})})()
    win32print = type('win32print', (), {'EnumPrinters': lambda *args: []})()
    WIN32_DISPONIBLE = False

# CLASE PRINTERMANAGER DEFINIDA CORRECTAMENTE
class PrinterManager:
    def __init__(self):
        self.printer = None
        self.printer_type = None
        self.config_exitosa = None
        self.ultima_factura = None  # Guardar última factura para reimpresión
        self.is_dig_ish58 = False

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
        """Intenta conexión usando driver Windows (spooler)."""
        if not WIN32_DISPONIBLE:
            print("Impresión Windows: pywin32 no disponible")
            return False
        try:
            printers = [p[2] for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL)]
            if printers:
                printer = Win32Raw(printers[0])
                self.printer = printer
                self.printer_type = "Windows"
                print(f"Conexión Windows: {printers[0]}")
                return True
        except Exception as e:
            print(f"Error Windows impresión: {e}")
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
                except Exception:
                    pass
                
                print("💰 Comandos de caja enviados - DIG ISH58")
                return True
            else:
                raise Exception("Impresora no conectada")
        except Exception as e:
            print(f"⚠️ Error al abrir caja: {e}")
            raise e

class App:
    def __init__(self, contenedor, ventana_raiz=None):
        """
        contenedor: Frame o ventana donde va la UI (grid/pack del POS).
        ventana_raiz: Toplevel/Tk para título, geometría y diálogos hijos; si es None, se usa contenedor.
        """
        self.ventana = contenedor
        self._toplevel = ventana_raiz if ventana_raiz is not None else contenedor
        self.setup_ventana()
        self.setup_variables()
        self.setup_datos()
        self.crear_interfaz()
        self.configurar_eventos()
        
        # Inicializar impresora - CON MEJOR MANEJO DE ERRORES
        self.printer_manager = None
        self.impresora_conectada = False

        if IMPRESION_DISPONIBLE:
            try:
                self.printer_manager = PrinterManager()
                # Conectar impresora al inicio
                self.conectar_impresora_async()
            except Exception as e:
                print(f"⚠️ Error inicializando impresora: {e}")
                messagebox.showwarning("Impresora", 
                                      "No se pudo inicializar el sistema de impresión.\n\n"
                                      "Instala las bibliotecas requeridas:\n"
                                      "pip install python-escpos pywin32 pyusb")
        else:
            print("ℹ️ Modo sin impresión - Bibliotecas no disponibles")

    def setup_ventana(self):
        """Título y fondo. El tamaño de la ventana lo ajusta 'Volver' / layout_responsive al abrir el módulo."""
        win = self._toplevel
        win.title("VmPOS · Punto de venta")
        win.configure(bg=T.POS_BG)
        self.ventana.configure(bg=T.POS_BG)
        self.setup_estilos()

    def setup_estilos(self):
        """ttk ligado a la ventana del POS (en Windows mejora estilos) + carrito con estilo propio."""
        top = self.ventana.winfo_toplevel()
        style = ttk.Style(top)
        style_ttk_treeview_pos(style, T.POS_BG)
        style_ttk_pos_carrito_treeview(style)

    def setup_variables(self):
        """Inicialización de variables de control"""
        self.documento = tk.StringVar()
        self.codigo_entrada = tk.StringVar()
        self.scan_info = tk.StringVar(value="")
        self.total_general = tk.DoubleVar(value=0.0)
        self.factura_num = datetime.now().strftime("%Y%m%d%H%M%S")
        self._scan_buffer = ""
        self._scan_last_ts = 0.0

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
        header = tk.Frame(self.ventana, bg=T.POS_HEADER, height=64)
        header.grid(row=0, column=0, columnspan=6, sticky="ew", padx=8, pady=(8, 4))
        header.grid_propagate(False)
        tk.Label(
            header,
            text="Punto de venta",
            font=(FONT, 16, "bold"),
            bg=T.POS_HEADER,
            fg=T.WHITE,
        ).pack(side="left", padx=20, pady=16)

        self.crear_info_frame()
        self.crear_input_frame()
        self.crear_botones()
        self.crear_botones_emergencia()
        self.crear_tabla()
        self.crear_total_frame()
        self.crear_botones_pago()
        for c in range(6):
            self.ventana.grid_columnconfigure(c, weight=1)
        # Que la zona del carrito (tabla) crezca con el alto del módulo (frame interior del canvas sync).
        self.ventana.grid_rowconfigure(5, weight=1)
        # Scroll global en ``preparar_ventana_modulo``; enlazar rueda y refrescar región.
        modulo_scroll_finalizar(self.ventana)

    def crear_info_frame(self):
        """Frame de información de factura"""
        info_frame = tk.Frame(self.ventana, bg=T.POS_BG)
        info_frame.grid(row=1, column=0, columnspan=6, sticky="ew", padx=10, pady=4)

        self.lbl_factura = tk.Label(
            info_frame,
            text=f"Factura: {self.factura_num}",
            font=F_BODY,
            bg=T.POS_BG,
            fg=T.POS_MUTED,
        )
        self.lbl_factura.grid(row=0, column=0, padx=10)

        self.lbl_fecha = tk.Label(info_frame, text="", font=F_BODY, bg=T.POS_BG, fg=T.POS_MUTED)
        self.lbl_fecha.grid(row=0, column=1, padx=10)

        self.lbl_hora = tk.Label(info_frame, text="", font=F_BODY, bg=T.POS_BG, fg=T.POS_MUTED)
        self.lbl_hora.grid(row=0, column=2, padx=10)

    def crear_input_frame(self):
        """Frame de inputs principales; una fila en pantallas anchas y dos en estrechas."""
        input_frame = tk.Frame(
            self.ventana, bg=T.POS_PANEL, highlightbackground=T.POS_BORDER, highlightthickness=1
        )
        input_frame.grid(row=2, column=0, columnspan=6, sticky="ew", padx=10, pady=8)
        self._input_frame_pos = input_frame

        self._lbl_doc = tk.Label(
            input_frame,
            text="Documento / cliente",
            font=F_BODY_B,
            bg=T.POS_PANEL,
            fg=T.POS_TEXT,
        )
        self.entry_doc = tk.Entry(input_frame, textvariable=self.documento, width=22, font=F_BODY)
        self._lbl_cod = tk.Label(
            input_frame, text="Código de barras", font=F_BODY_B, bg=T.POS_PANEL, fg=T.POS_TEXT
        )
        self.entry_codigo = tk.Entry(input_frame, textvariable=self.codigo_entrada, width=18, font=F_BODY)
        self._lbl_scan_info = tk.Label(
            input_frame,
            textvariable=self.scan_info,
            font=F_SMALL,
            bg=T.POS_PANEL,
            fg=T.POS_MUTED,
            anchor="w",
        )

        self._input_sched = None
        self._input_last_mode = None
        self._apply_input_layout()
        input_frame.bind("<Configure>", self._schedule_input_layout)

    def _schedule_input_layout(self, event):
        if event.widget is not getattr(self, "_input_frame_pos", None):
            return
        if getattr(self, "_input_sched", None) is not None:
            try:
                self.ventana.after_cancel(self._input_sched)
            except (tk.TclError, Exception):
                pass
        self._input_sched = self.ventana.after(70, self._apply_input_layout)

    def _apply_input_layout(self):
        self._input_sched = None
        fr = getattr(self, "_input_frame_pos", None)
        if fr is None:
            return
        try:
            w = int(fr.winfo_width())
        except (tk.TclError, Exception):
            return
        if w <= 1:
            return
        wide = w >= 540
        if self._input_last_mode is not None and wide == self._input_last_mode:
            return
        self._input_last_mode = wide

        for wdg in (self._lbl_doc, self.entry_doc, self._lbl_cod, self.entry_codigo, self._lbl_scan_info):
            wdg.grid_forget()

        if wide:
            fr.columnconfigure(0, weight=0)
            fr.columnconfigure(1, weight=1)
            fr.columnconfigure(2, weight=0)
            fr.columnconfigure(3, weight=1)
            self._lbl_doc.grid(row=0, column=0, padx=10, pady=10, sticky="w")
            self.entry_doc.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
            self._lbl_cod.grid(row=0, column=2, padx=10, pady=10)
            self.entry_codigo.grid(row=0, column=3, padx=10, pady=10, sticky="ew")
            self._lbl_scan_info.grid(row=1, column=0, columnspan=4, padx=10, pady=(0, 8), sticky="w")
        else:
            for c in range(4):
                fr.columnconfigure(c, weight=0)
            fr.columnconfigure(1, weight=1)
            self._lbl_doc.grid(row=0, column=0, padx=10, pady=(10, 4), sticky="nw")
            self.entry_doc.grid(row=0, column=1, padx=10, pady=(10, 4), sticky="ew")
            self._lbl_cod.grid(row=1, column=0, padx=10, pady=(4, 10), sticky="nw")
            self.entry_codigo.grid(row=1, column=1, padx=10, pady=(4, 10), sticky="ew")
            self._lbl_scan_info.grid(row=2, column=0, columnspan=2, padx=10, pady=(0, 8), sticky="w")

    def crear_botones(self):
        """Botones de acción: una fila de cuatro en pantalla ancha; apilados si es estrecha."""
        button_frame = tk.Frame(self.ventana, bg=T.POS_BG)
        button_frame.grid(row=3, column=0, columnspan=6, pady=8, sticky="ew", padx=10)
        self._button_frame_pos = button_frame

        botones = [
            ("Buscar producto", self.buscar_producto, T.STAT_1),
            ("Añadir servicio", self.anadir_servicio, T.ACCENT),
            ("Quitar línea", self.eliminar_seleccionado, T.DANGER),
        ]

        self._btns_principales = []
        for texto, comando, color in botones:
            btn = tk.Button(
                button_frame,
                text=texto,
                command=comando,
                bg=color,
                fg=T.WHITE,
                font=F_BODY_B,
                padx=12,
                pady=6,
                relief="flat",
                cursor="hand2",
            )
            self._btns_principales.append(btn)

        self._btn_mirar = tk.Button(
            button_frame,
            text="Mirar factura",
            command=self.mirar_factura,
            bg=T.POS_HEADER,
            fg=T.WHITE,
            font=F_BODY_B,
            padx=16,
            pady=6,
            relief="flat",
            cursor="hand2",
        )

        _fila_accion = self._btns_principales + [self._btn_mirar]
        bind_reflow_grid_uniform(
            button_frame,
            _fila_accion,
            columnas_cuando_anchas=4,
            umbral=560,
            debounce_ms=80,
            pad_exterior=10,
        )

    def crear_botones_emergencia(self):
        """Caja registradora e impresión rápida"""
        emergency_frame = tk.Frame(
            self.ventana,
            bg=T.POS_EMERGENCY_BG,
            highlightbackground=T.POS_EMERGENCY_BORDER,
            highlightthickness=1,
        )
        emergency_frame.grid(row=4, column=0, columnspan=6, sticky="ew", padx=10, pady=4)

        tk.Label(
            emergency_frame,
            text="Impresora y caja",
            font=F_BODY_B,
            bg=T.POS_EMERGENCY_BG,
            fg=T.WARN,
        ).pack(pady=(6, 4))

        btn_frame = tk.Frame(emergency_frame, bg=T.POS_EMERGENCY_BG)
        btn_frame.pack(pady=(0, 8))

        btn_abrir_caja = tk.Button(
            btn_frame,
            text="Abrir caja",
            command=self.emergencia_abrir_caja,
            bg=T.POS_EMERGENCY_BG,
            fg=T.WARN,
            font=F_SMALL,
            padx=12,
            pady=4,
            relief="solid",
            bd=1,
            cursor="hand2",
        )

        btn_reimprimir = tk.Button(
            btn_frame,
            text="Reimprimir última",
            command=self.emergencia_reimprimir,
            bg=T.POS_EMERGENCY_BG,
            fg=T.POS_TEXT,
            font=F_SMALL,
            padx=12,
            pady=4,
            relief="solid",
            bd=1,
            cursor="hand2",
        )

        bind_reflow_pack(
            btn_frame,
            [
                (btn_abrir_caja, {"side": tk.LEFT, "padx": 6}, {"fill": tk.X, "pady": 4}),
                (btn_reimprimir, {"side": tk.LEFT, "padx": 6}, {"fill": tk.X, "pady": 4}),
            ],
            umbral=480,
            debounce_ms=80,
        )

    def crear_tabla(self):
        """Crear tabla de productos; altura fija (el panel completo hace scroll si la ventana es baja)."""
        tabla_frame = tk.Frame(self.ventana, bg=T.POS_BG)
        tabla_frame.grid(row=5, column=0, columnspan=6, padx=10, pady=8, sticky="nsew")

        tk.Label(
            tabla_frame,
            text="Carrito",
            font=F_SUB,
            bg=T.POS_BG,
            fg=T.POS_TEXT,
        ).pack(anchor="w", pady=(0, 6))
        wrap = tk.Frame(tabla_frame, bg=T.POS_BG)
        wrap.pack(fill=tk.BOTH, expand=True)

        self.tabla = ttk.Treeview(
            wrap,
            columns=("Producto", "Precio", "Cantidad", "Total"),
            show="headings",
            height=6,
            style="POSCarrito.Treeview",
        )

        for col in ("Producto", "Precio", "Cantidad", "Total"):
            self.tabla.heading(col, text=col)
            self.tabla.column(col, width=160, minwidth=60, anchor="center", stretch=True)

        vsb = ttk.Scrollbar(wrap, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=vsb.set)
        self.tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

    def crear_total_frame(self):
        """Frame del total"""
        total_frame = tk.Frame(self.ventana, bg=T.POS_TOTAL_BAR, relief="flat")
        total_frame.grid(row=6, column=0, columnspan=6, sticky="ew", padx=10, pady=8)

        tk.Label(
            total_frame,
            text="TOTAL",
            font=(FONT, 14, "bold"),
            bg=T.POS_TOTAL_BAR,
            fg=T.WHITE,
        ).pack(side="left", padx=20, pady=12)

        self.total_label = tk.Label(
            total_frame,
            text=self.formato_peso(0),
            font=(FONT, 18, "bold"),
            bg=T.POS_TOTAL_BAR,
            fg=T.WHITE,
        )
        self.total_label.pack(side="right", padx=20, pady=12)

    def crear_botones_pago(self):
        """Botones de pago y nueva venta: misma fila en ancho; apilados en estrecho."""
        payment_frame = tk.Frame(self.ventana, bg=T.POS_BG)
        payment_frame.grid(row=7, column=0, columnspan=6, pady=12, sticky="ew", padx=10)

        btn_pagar = tk.Button(
            payment_frame,
            text="Procesar pago",
            command=self.pagar,
            bg=T.POS_BTN_GO,
            fg=T.WHITE,
            font=(FONT, 12, "bold"),
            padx=24,
            pady=12,
            relief="flat",
            cursor="hand2",
            activebackground=T.POS_BTN_GO_HOVER,
        )
        btn_nueva = tk.Button(
            payment_frame,
            text="Nueva venta",
            command=self.limpiar_formulario,
            bg=T.POS_BTN_ALT,
            fg=T.WHITE,
            font=F_BODY,
            padx=16,
            pady=6,
            relief="flat",
            cursor="hand2",
        )
        bind_reflow_pack(
            payment_frame,
            [
                (
                    btn_pagar,
                    {"side": tk.LEFT, "padx": 4, "expand": True, "fill": tk.BOTH},
                    {"fill": tk.X, "pady": 4},
                ),
                (
                    btn_nueva,
                    {"side": tk.LEFT, "padx": 4, "expand": True, "fill": tk.BOTH},
                    {"fill": tk.X, "pady": 4},
                ),
            ],
            umbral=440,
            debounce_ms=80,
        )

    def configurar_eventos(self):
        """Configurar eventos de teclado y focus"""
        self.entry_codigo.bind('<Return>', lambda e: self.escanear_codigo())
        self.entry_codigo.bind('<KeyRelease>', self.on_codigo_change)
        # Captura global para lectores tipo keyboard-wedge (timbran y envían Enter).
        self.ventana.bind_all("<KeyPress>", self._capturar_scanner_global, add="+")
        self.entry_doc.focus()
        self.actualizar_hora()

    def _capturar_scanner_global(self, event):
        """
        Captura secuencias rápidas del lector aunque el foco no esté en el campo de código.
        No interfiere con escritura manual normal en formularios.
        """
        try:
            import time
            now = time.time()
            if event.keysym == "Return":
                buf = (self._scan_buffer or "").strip()
                self._scan_buffer = ""
                self._scan_last_ts = now
                if len(buf) >= 3:
                    self.codigo_entrada.set(buf)
                    self.escanear_codigo()
                    return "break"
                return None

            ch = event.char or ""
            if len(ch) == 1 and ch.isprintable():
                # Si pasan muchos ms entre teclas, se asume que fue digitación manual.
                if now - float(self._scan_last_ts or 0) > 0.18:
                    self._scan_buffer = ""
                self._scan_buffer += ch
                self._scan_last_ts = now
        except Exception:
            return None
        return None

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
            error_window = tk.Toplevel(self._toplevel)
            error_window.title("Error — caja registradora")
            error_window.configure(bg=T.BG_APP)
            error_window.grab_set()
            centrar_ventana(error_window, 500, 300, self._toplevel)

            tk.Label(
                error_window,
                text="No se pudo abrir la caja",
                font=F_SUB,
                bg=T.BG_APP,
                fg=T.DANGER,
            ).pack(pady=10)

            tk.Label(
                error_window,
                text=f"Error: {error_detallado}",
                font=F_SMALL,
                bg=T.BG_APP,
                fg=T.POS_TEXT,
                wraplength=450,
            ).pack(pady=5)

            tk.Label(
                error_window,
                text="Compruebe cable RJ11/RJ12 e impresora encendida.",
                font=F_SMALL,
                bg=T.BG_APP,
                fg=T.POS_MUTED,
            ).pack(pady=(10, 5))

            soluciones = """• Caja conectada al puerto de la impresora\n• Cable RJ11/RJ12 bien insertado\n• Reiniciar impresora si persiste"""

            tk.Label(error_window, text=soluciones, font=F_SMALL, bg=T.BG_APP, fg=T.POS_TEXT, justify="left").pack(
                pady=5
            )
            
            def reintentar_caja():
                error_window.destroy()
                print("DEBUG: Reintentando apertura de caja...")
                try:
                    # FORZAR NUEVA CONEXIÓN
                    self.impresora_conectada = False
                    self.emergencia_abrir_caja()
                except Exception as retry_error:
                    messagebox.showerror("Error", f"Reintento falló: {retry_error}")
            
            btn_frame = tk.Frame(error_window, bg=T.BG_APP)
            btn_frame.pack(pady=15)

            tk.Button(
                btn_frame,
                text="Reintentar",
                command=reintentar_caja,
                bg=T.WARN,
                fg=T.WHITE,
                font=F_BODY_B,
                padx=15,
                relief="flat",
                cursor="hand2",
            ).pack(side="left", padx=5)

            tk.Button(
                btn_frame,
                text="Cerrar",
                command=error_window.destroy,
                bg=T.POS_BTN_ALT,
                fg=T.WHITE,
                font=F_BODY_B,
                padx=15,
                relief="flat",
                cursor="hand2",
            ).pack(side="left", padx=5)
    
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
    #   FUNCIONES DE DATOS AND UTILIDADES
    # ====================================================================================

    def obtener_productos(self):
        """(codigo, nombre, stock, precio, tipo, referencia)."""
        try:
            with sqlite3.connect(ventas_db_path()) as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        """
                        SELECT codigo, nombre, stock, precio, COALESCE(tipo, 'producto'),
                               TRIM(COALESCE(referencia, ''))
                        FROM productos
                        """
                    )
                    return cursor.fetchall()
                except sqlite3.OperationalError:
                    try:
                        cursor.execute(
                            "SELECT codigo, nombre, stock, precio, COALESCE(tipo, 'producto') FROM productos"
                        )
                    except sqlite3.OperationalError:
                        cursor.execute("SELECT codigo, nombre, stock, precio FROM productos")
                    out = []
                    for r in cursor.fetchall():
                        if len(r) == 4:
                            out.append((r[0], r[1], r[2], r[3], "producto", ""))
                        else:
                            out.append((r[0], r[1], r[2], r[3], r[4], ""))
                    return out
        except Exception as e:
            msg = str(e).lower()
            if "no such table: productos" in msg:
                messagebox.showerror("Inventario", "No hay producto en el stock")
            else:
                messagebox.showerror("Error DB", f"Error de base de datos: {e}")
            return []

    def formato_peso(self, valor):
        """Formato de pesos colombianos"""
        return f"${int(valor):,.0f} COP"

    def limpiar_precio(self, texto):
        """Convertir texto de precio a número"""
        if isinstance(texto, (int, float)):
            return float(texto)
        if not isinstance(texto, str):
            return 0.0
        try:
            return float(str(texto).replace("$", "").replace("COP", "").replace(",", "").strip() or 0)
        except (ValueError, AttributeError):
            return 0.0
        
    def actualizar_total(self):
        """Actualizar el display del total"""
        self.total_label.config(text=self.formato_peso(self.total_general.get()))

    def actualizar_hora(self):
        """Actualizar hora cada segundo"""
        ahora = datetime.now()
        self.lbl_fecha.config(text=ahora.strftime("%d-%m-%Y"))
        self.lbl_hora.config(text=ahora.strftime("%H:%M:%S"))
        self.ventana.after(1000, self.actualizar_hora)

    # ====================================================================================
    #   FUNCIONES DE INTERFAZ - MEJORADAS
    # ====================================================================================

    def buscar_producto(self):
        """Ventana de búsqueda de productos"""
        ventana = tk.Toplevel(self._toplevel)
        ventana.title("Buscar producto")
        ventana.configure(bg=T.POS_BG)
        ventana.grab_set()
        centrar_ventana(ventana, 700, 500, self._toplevel)

        filtro = tk.StringVar()
        tk.Label(ventana, text="Filtrar por nombre o código", bg=T.POS_BG, fg=T.POS_TEXT, font=F_BODY_B).pack(
            pady=10
        )

        entry = tk.Entry(ventana, textvariable=filtro, width=50, font=F_BODY)
        entry.pack(pady=5)
        entry.focus()

        lista = ttk.Treeview(
            ventana, columns=("Código", "Nombre", "Stock", "Precio"), show="headings", height=15
        )
        for col in ("Código", "Nombre", "Stock", "Precio"):
            lista.heading(col, text=col)
            lista.column(col, width=150, anchor="center")
        lista.pack(padx=10, pady=10)

        def actualizar_lista():
            lista.delete(*lista.get_children())
            filtro_texto = filtro.get().lower()
            
            for r in self.productos_inventario:
                if len(r) >= 5:
                    codigo, nombre, stock, precio, tipo = (
                        r[0],
                        r[1],
                        r[2],
                        r[3],
                        (r[4] or "producto").lower(),
                    )
                else:
                    codigo, nombre, stock, precio, tipo = r[0], r[1], r[2], r[3], "producto"
                ref = (r[5] if len(r) > 5 else "") or ""
                if not filtro_texto or filtro_texto in f"{codigo} {nombre} {ref}".lower():
                    stock_txt = "—" if tipo == "servicio" else stock
                    lista.insert(
                        "", tk.END, values=(codigo, nombre, stock_txt, self.formato_peso(precio))
                    )

        def seleccionar():
            item = lista.focus()
            if not item:
                return
            valores = lista.item(item)["values"]
            codigo = valores[0]
            nombre = valores[1]
            stock_raw = valores[2]
            precio = self.limpiar_precio(valores[3])
            if str(stock_raw) == "—":
                self.agregar_producto(codigo, nombre, precio)
                ventana.destroy()
                return
            try:
                s = int(stock_raw)
            except (TypeError, ValueError):
                s = 0
            if s > 0:
                self.agregar_producto(codigo, nombre, precio)
                ventana.destroy()
            else:
                messagebox.showwarning("Sin stock", "Producto sin stock disponible")

        actualizar_lista()
        filtro.trace("w", lambda *args: actualizar_lista())
        
        tk.Button(
            ventana,
            text="Seleccionar",
            command=seleccionar,
            bg=T.POS_BTN_GO,
            fg=T.WHITE,
            font=F_BODY_B,
            padx=20,
            pady=8,
            relief="flat",
            cursor="hand2",
        ).pack(pady=10)
        
        ventana.bind('<Return>', lambda e: seleccionar())

    def anadir_servicio(self):
        """
        Añade una línea de servicio (recargas, copias, etc.) sin inventario.
        En factura/detalle se guarda con código N/A y no descuenta stock.
        """
        w = tk.Toplevel(self._toplevel)
        w.title("Añadir servicio u otro cargo")
        w.configure(bg=T.POS_BG)
        w.grab_set()
        w.resizable(False, False)
        centrar_ventana(w, 440, 340, self._toplevel)

        v_nombre = tk.StringVar()
        v_ref = tk.StringVar()
        v_valor = tk.StringVar()

        tk.Label(
            w,
            text="Servicio u otro cargo (no descontará inventario)",
            font=F_BODY_B,
            bg=T.POS_BG,
            fg=T.POS_TEXT,
        ).pack(pady=(16, 8))

        frm = tk.Frame(w, bg=T.POS_BG)
        frm.pack(padx=24, pady=8, fill="x")

        def fila(lbl, r, var, show=None):
            tk.Label(frm, text=lbl, font=F_BODY, bg=T.POS_BG, fg=T.POS_MUTED, anchor="w").grid(
                row=r, column=0, sticky="w", pady=6
            )
            e = tk.Entry(frm, textvariable=var, font=F_BODY, width=36, show=show)
            e.grid(row=r, column=1, sticky="ew", pady=6, padx=(12, 0))
            return e

        fila("Nombre *", 0, v_nombre)
        fila("Referencia (opcional)", 1, v_ref)
        e_val = fila("Valor (COP) *", 2, v_valor)
        frm.grid_columnconfigure(1, weight=1)

        hint = tk.Label(
            w,
            text="Ej.: recarga, minutos, tarea express…",
            font=F_SMALL,
            bg=T.POS_BG,
            fg=T.POS_MUTED,
        )
        hint.pack()
        e_val.focus()
        w.bind("<Return>", lambda e: _ok())

        def _ok():
            nombre = (v_nombre.get() or "").strip()
            ref = (v_ref.get() or "").strip()
            raw = (v_valor.get() or "").strip()
            if not nombre:
                messagebox.showwarning("Nombre", "Indica el nombre del servicio o cargo.", parent=w)
                return
            try:
                precio = self.limpiar_precio(raw)
                if precio < 0:
                    raise ValueError
            except (TypeError, ValueError):
                messagebox.showwarning("Valor", "Escribe un valor numérico válido (ej. 5000 o 5.000).", parent=w)
                return
            if precio <= 0:
                messagebox.showwarning("Valor", "El valor debe ser mayor a cero.", parent=w)
                return

            if ref:
                linea = f"🔧 {nombre}  |  Ref: {ref}"
            else:
                linea = f"🔧 {nombre}"

            self.tabla.insert(
                "",
                tk.END,
                values=(linea, self.formato_peso(precio), 1, self.formato_peso(precio)),
            )
            self.total_general.set(self.total_general.get() + precio)
            self.actualizar_total()
            w.destroy()

        def _cancel():
            w.destroy()

        bar = tk.Frame(w, bg=T.POS_BG)
        bar.pack(pady=20)
        tk.Button(
            bar,
            text="Añadir al carrito",
            command=_ok,
            bg=T.POS_BTN_GO,
            fg=T.WHITE,
            font=F_BODY_B,
            padx=16,
            pady=8,
            relief="flat",
            cursor="hand2",
        ).pack(side="left", padx=4)
        tk.Button(
            bar,
            text="Cancelar",
            command=_cancel,
            bg=T.POS_BTN_ALT,
            fg=T.WHITE,
            font=F_BODY,
            padx=12,
            pady=8,
            relief="flat",
            cursor="hand2",
        ).pack(side="left", padx=4)

    def _ventas_fetch_rows(self, filtro_doc):
        """Devuelve (filas, error). Compat. con tablas antiguas sin columna `id` (usa rowid)."""
        try:
            with sqlite3.connect(ventas_db_path()) as conn:
                ensure_fiado_schema(conn)
                return _ventas_select_rows(conn, filtro_doc)
        except Exception as e:
            return [], str(e)

    def _texto_detalle_factura_por_id(self, id_venta):
        """Cabecera y líneas; funciona con id o rowid; muestra productos embebidos en tablas antiguas."""
        try:
            with sqlite3.connect(ventas_db_path()) as conn:
                ensure_fiado_schema(conn)
                names = _ventas_column_set(conn)
                if not names:
                    return "No hay tabla de ventas."
                pk = "id" if "id" in names else "rowid"
                c = conn.cursor()
                if "fecha_venta" in names:
                    fe = "fecha_venta"
                else:
                    fe = "fecha"
                he = "hora_venta" if "hora_venta" in names else ("hora" if "hora" in names else "''")
                if "documento_cliente" in names:
                    dc = "documento_cliente"
                else:
                    dc = "cedula" if "cedula" in names else "''"
                if "total_venta" in names and "total" in names:
                    tot = "COALESCE(total_venta, total, 0)"
                elif "total_venta" in names:
                    tot = "total_venta"
                else:
                    tot = "total" if "total" in names else "0"
                if "tipo_pago" in names:
                    tip = "COALESCE(LOWER(tipo_pago), 'contado')"
                elif "metodo_pago" in names:
                    tip = "COALESCE(LOWER(metodo_pago), 'contado')"
                else:
                    tip = "'contado'"

                c.execute(
                    f"""
                    SELECT {pk} AS vpk, {fe}, {he}, {dc}, {tot}, {tip}
                    FROM ventas
                    WHERE {pk} = ?
                    """,
                    (id_venta,),
                )
                v = c.fetchone()
                if not v:
                    return "No se encontró la venta."
                vid, fdate, ftime, doc, ttot, tipv = v
                doc = (str(doc) if doc is not None else "").strip() or "—"
                c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='detalle_ventas'")
                if c.fetchone():
                    dcols = _detalle_ventas_column_set(conn)
                    ord_col = "id" if dcols and "id" in dcols else "rowid"
                    c.execute(
                        f"""
                        SELECT nombre_producto, precio_unitario, cantidad, subtotal
                        FROM detalle_ventas
                        WHERE id_venta = ?
                        ORDER BY {ord_col}
                        """,
                        (id_venta,),
                    )
                    lineas = c.fetchall()
                else:
                    lineas = []
                prods_text = None
                if "productos" in names and (not lineas):
                    c.execute(f"SELECT productos FROM ventas WHERE {pk} = ?", (id_venta,))
                    pr = c.fetchone()
                    if pr and pr[0]:
                        prods_text = str(pr[0])
        except Exception as e:
            return f"Error: {e}"

        out = [
            f"ID / ref.: {vid}",
            f"Fecha: {fdate}   Hora: {ftime or '—'}",
            f"Documento: {doc}",
            f"Total: {self.formato_peso(float(ttot or 0))}  ·  Tipo: {tipv}",
            "—" * 40,
        ]
        for nombre, p_u, ctd, sub in lineas:
            out.append(f"• {nombre}")
            out.append(
                f"   {int(ctd) if ctd == int(ctd) else ctd} × {self.formato_peso(p_u)}  =  {self.formato_peso(sub)}"
            )
        if prods_text:
            out.append("\nGuardado (histórico):")
            out.append(prods_text)
        if not lineas and not prods_text:
            out.append("(Sin líneas de detalle en la base de datos.)")
        return "\n".join(out)

    def _datos_venta_desde_id(self, id_venta):
        """Arma el dict que espera ``PrinterManager.imprimir_factura`` (reimpresión desde historial)."""
        try:
            with sqlite3.connect(ventas_db_path()) as conn:
                ensure_fiado_schema(conn)
                names = _ventas_column_set(conn)
                if not names:
                    return None
                pk = "id" if "id" in names else "rowid"
                c = conn.cursor()
                if "fecha_venta" in names:
                    fe = "fecha_venta"
                else:
                    fe = "fecha"
                he = "hora_venta" if "hora_venta" in names else ("hora" if "hora" in names else "''")
                if "documento_cliente" in names:
                    dc = "documento_cliente"
                else:
                    dc = "cedula" if "cedula" in names else "''"
                if "total_venta" in names and "total" in names:
                    tot = "COALESCE(total_venta, total, 0)"
                elif "total_venta" in names:
                    tot = "total_venta"
                else:
                    tot = "total" if "total" in names else "0"
                c.execute(
                    f"""
                    SELECT {pk} AS vpk, {fe}, {he}, {dc}, {tot}
                    FROM ventas
                    WHERE {pk} = ?
                    """,
                    (id_venta,),
                )
                v = c.fetchone()
                if not v:
                    return None
                vid, fdate, ftime, doc, ttot = v
                doc = (str(doc) if doc is not None else "").strip() or "—"
                fs = str(fdate) if fdate is not None else ""
                fecha_dmY = fs[:10] if len(fs) >= 10 else fs
                if len(fs) >= 10 and fs[4] == "-":
                    try:
                        fecha_dmY = datetime.strptime(fs[:10], "%Y-%m-%d").strftime("%d-%m-%Y")
                    except ValueError:
                        pass
                hora_s = (str(ftime) if ftime is not None else "")[:12]
                lineas = []
                c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='detalle_ventas'")
                if c.fetchone():
                    dcols = _detalle_ventas_column_set(conn)
                    ord_col = "id" if dcols and "id" in dcols else "rowid"
                    c.execute(
                        f"""
                        SELECT nombre_producto, precio_unitario, cantidad, subtotal
                        FROM detalle_ventas
                        WHERE id_venta = ?
                        ORDER BY {ord_col}
                        """,
                        (id_venta,),
                    )
                    lineas = c.fetchall()
                prods_text = None
                if "productos" in names and (not lineas):
                    c.execute(f"SELECT productos FROM ventas WHERE {pk} = ?", (id_venta,))
                    pr = c.fetchone()
                    if pr and pr[0]:
                        prods_text = str(pr[0])
                productos = []
                for nombre, p_u, ctd, _sub in lineas:
                    try:
                        productos.append((str(nombre), float(p_u or 0), int(ctd) if ctd is not None else 1))
                    except (TypeError, ValueError):
                        productos.append((str(nombre), 0.0, 1))
                if not productos and prods_text:
                    try:
                        tv = float(ttot or 0)
                    except (TypeError, ValueError):
                        tv = 0.0
                    txt = (prods_text or "")[:80]
                    productos = [(txt + ("…" if len(prods_text) > 80 else ""), tv, 1)]
                if not productos:
                    try:
                        tv = float(ttot or 0)
                    except (TypeError, ValueError):
                        tv = 0.0
                    productos = [("(Sin líneas de detalle)", tv, 1)]
                try:
                    total = float(ttot or 0)
                except (TypeError, ValueError):
                    total = 0.0
                return {
                    "factura": str(vid),
                    "fecha": fecha_dmY,
                    "hora": hora_s,
                    "cliente": doc,
                    "productos": productos,
                    "total": total,
                }
        except Exception as e:
            print(f"_datos_venta_desde_id: {e}")
            return None

    @staticmethod
    def _texto_vista_ticket(d):
        """Mismo diseño de ticket que la impresora térmica (vista previa)."""
        lines = [
            "        VARIEDADES MARCE\n",
            "    Centro de copiado y belleza\n",
            "       Cel: 300-123-4567\n",
            "=" * 32 + "\n",
            f"Factura: {d['factura']}\n",
            f"Fecha: {d['fecha']}\n",
            f"Hora: {d['hora']}\n",
            f"Cliente: {d['cliente']}\n",
            "-" * 32 + "\n",
            "Producto           Cant  Precio\n",
            "-" * 32 + "\n",
        ]
        total_items = 0
        for nombre, precio, cantidad in d["productos"]:
            subtotal = precio * cantidad
            total_items += cantidad
            nombre_corto = nombre[:15].ljust(15)
            lines.append(f"{nombre_corto} {cantidad:>2}x ${precio:>6,.0f}\n")
            if cantidad > 1:
                lines.append(f"      Subtotal: ${subtotal:>8,.0f}\n")
        lines.append("-" * 32 + "\n")
        lines.append(f"Total Items: {total_items}\n")
        lines.append(f"TOTAL: ${d['total']:>16,.0f}\n")
        lines.append("=" * 32 + "\n")
        lines.append("     Gracias por tu compra!\n")
        lines.append("        Vuelve pronto\n")
        return "".join(lines)

    def _ventas_cargar_enriquecido(self, filtro_doc):
        """Todas las ventas con columna nombre (cliente o primer producto). (filas, error)."""
        try:
            with sqlite3.connect(ventas_db_path()) as conn:
                ensure_fiado_schema(conn)
                rows, err = _ventas_select_rows(conn, filtro_doc)
                if err:
                    return None, err
                return _ventas_enriquecer_nombres(conn, rows), None
        except Exception as e:
            return None, str(e)

    def mirar_factura(self):
        """Lista de ventas del día (por defecto hoy); elige otro día en el desplegable; filtra por documento."""
        win = tk.Toplevel(self._toplevel)
        win.title("Ventas del día")
        win.configure(bg=T.POS_BG)
        win.grab_set()
        centrar_ventana(win, 700, 440, self._toplevel)
        hoy_ymd = date.today().strftime("%Y-%m-%d")
        st = {"todo": [], "label_to_ymd": {}}
        vdoc = tk.StringVar(value=(self.documento.get() or "").strip())
        vdia = tk.StringVar()
        fr = tk.Frame(win, bg=T.POS_BG)
        fr.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)
        t1 = tk.Frame(fr, bg=T.POS_BG)
        t1.pack(fill=tk.X, pady=(0, 2))
        tk.Label(t1, text="Día:", font=F_SMALL, bg=T.POS_BG, fg=T.POS_TEXT).pack(side=tk.LEFT, padx=(0, 4))
        cb_dia = ttk.Combobox(t1, textvariable=vdia, state="readonly", width=36)
        cb_dia.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        btn_hoy = tk.Button(
            t1, text="Hoy", font=F_SMALL, bg=T.STAT_1, fg=T.WHITE, padx=8, pady=2, relief="flat", cursor="hand2"
        )
        btn_hoy.pack(side=tk.LEFT, padx=4)
        t2 = tk.Frame(fr, bg=T.POS_BG)
        t2.pack(fill=tk.X, pady=2)
        tk.Label(t2, text="Documento:", font=F_SMALL, bg=T.POS_BG, fg=T.POS_MUTED).pack(side=tk.LEFT, padx=(0, 4))
        ent_doc = tk.Entry(t2, textvariable=vdoc, width=18, font=F_BODY)
        ent_doc.pack(side=tk.LEFT, padx=2)
        btn_f = tk.Button(
            t2, text="Aplicar", font=F_SMALL, bg=T.POS_BTN_GO, fg=T.WHITE, padx=8, pady=2, relief="flat", cursor="hand2"
        )
        btn_f.pack(side=tk.LEFT, padx=4)
        lbl_tit = tk.Label(fr, text="", font=F_SMALL, bg=T.POS_BG, fg=T.POS_TEXT, anchor="w", justify="left")
        lbl_tit.pack(fill=tk.X, pady=2)
        tw = ttk.Frame(fr)
        tw.pack(fill=tk.BOTH, expand=True, pady=2)
        ysb = ttk.Scrollbar(tw, orient=tk.VERTICAL)
        cols = ("ref", "nombre", "doc", "valor", "hora", "fventa")
        tree = ttk.Treeview(
            tw, columns=cols, show="headings", height=9, selectmode="browse"
        )
        tree.heading("ref", text="Ref.")
        tree.heading("nombre", text="Nombre")
        tree.heading("doc", text="Doc.")
        tree.heading("valor", text="Valor")
        tree.heading("hora", text="Hora")
        tree.heading("fventa", text="Fecha")
        tree.column("ref", width=70, minwidth=50, stretch=False)
        tree.column("nombre", width=160, minwidth=60, stretch=True, anchor="w")
        tree.column("doc", width=100, minwidth=50, stretch=False, anchor="w")
        tree.column("valor", width=100, minwidth=60, stretch=False, anchor="e")
        tree.column("hora", width=70, minwidth=50, stretch=False, anchor="center")
        tree.column("fventa", width=90, minwidth=70, stretch=False, anchor="center")
        try:
            style_ttk_treeview_pos(ttk.Style(), T.POS_BG)
        except (tk.TclError, Exception):
            pass
        tree.grid(row=0, column=0, sticky="nsew")
        ysb.grid(row=0, column=1, sticky="ns")
        ysb.config(command=tree.yview)
        tree.configure(yscrollcommand=ysb.set)
        tw.rowconfigure(0, weight=1)
        tw.columnconfigure(0, weight=1)
        fbtn = tk.Frame(fr, bg=T.POS_BG)
        fbtn.pack(fill=tk.X, pady=(2, 0))
        tk.Label(fbtn, text="Resumen:", font=F_SMALL, bg=T.POS_BG, fg=T.POS_MUTED).pack(side=tk.LEFT, padx=(0, 4))
        btn_ver = tk.Button(
            fbtn, text="Ver factura", font=F_SMALL, bg=T.STAT_2, fg=T.WHITE, padx=8, pady=2, relief="flat", cursor="hand2"
        )
        btn_ver.pack(side=tk.LEFT, padx=2)
        btn_imp = tk.Button(
            fbtn, text="Imprimir factura", font=F_SMALL, bg=T.POS_ACCENT, fg=T.WHITE, padx=8, pady=2, relief="flat", cursor="hand2"
        )
        btn_imp.pack(side=tk.LEFT, padx=2)
        txf = tk.Frame(fr, bg=T.POS_BG)
        txf.pack(fill=tk.BOTH, pady=2)
        sbd = ttk.Scrollbar(txf)
        txt = tk.Text(txf, height=4, font=F_SMALL, bg=T.BG_SUBTLE, fg=T.POS_TEXT, wrap="word", relief="flat")
        sbd.pack(side=tk.RIGHT, fill=tk.Y)
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        txt.config(yscrollcommand=sbd.set, state=tk.DISABLED)
        sbd.config(command=txt.yview)
        bfoot = tk.Frame(fr, bg=T.POS_BG)
        bfoot.pack(fill=tk.X, pady=(2, 0))
        tk.Button(
            bfoot, text="Cerrar", command=win.destroy, font=F_SMALL, bg=T.POS_BTN_ALT, fg=T.WHITE, padx=12, pady=3,
            relief="flat", cursor="hand2",
        ).pack(side=tk.RIGHT)

        def _id_venta_sel():
            s = tree.selection()
            if not s or not str(s[0]).startswith("v"):
                return None
            return int(str(s[0])[1:])

        def abrir_ver_factura():
            vid = _id_venta_sel()
            if vid is None:
                messagebox.showinfo("Ver factura", "Selecciona una venta en la lista.", parent=win)
                return
            d = self._datos_venta_desde_id(vid)
            if not d:
                messagebox.showerror("Error", "No se pudo cargar la factura.", parent=win)
                return
            wv = tk.Toplevel(win)
            wv.title(f"Factura {d['factura']}")
            wv.configure(bg=T.POS_BG)
            wv.transient(win)
            centrar_ventana(wv, 400, 460, win)
            fwrap = tk.Frame(wv, bg=T.POS_BG)
            fwrap.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
            sbv = ttk.Scrollbar(fwrap)
            tv = tk.Text(
                fwrap, width=42, height=22, font=("Consolas", 9), bg=T.BG_CARD, fg=T.POS_TEXT, wrap="word", relief="flat"
            )
            sbv.pack(side=tk.RIGHT, fill=tk.Y)
            tv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            tv.insert(tk.END, self._texto_vista_ticket(d))
            tv.config(state=tk.DISABLED)
            tv.config(yscrollcommand=sbv.set)
            sbv.config(command=tv.yview)
            tk.Button(
                wv, text="Cerrar", command=wv.destroy, font=F_SMALL, bg=T.POS_BTN_ALT, fg=T.WHITE, padx=12, pady=4,
                relief="flat", cursor="hand2",
            ).pack(pady=4)
            wv.grab_set()

        def imprimir_seleccionada():
            vid = _id_venta_sel()
            if vid is None:
                messagebox.showinfo("Imprimir", "Selecciona una venta en la lista.", parent=win)
                return
            d = self._datos_venta_desde_id(vid)
            if not d:
                messagebox.showerror("Error", "No se pudo cargar la factura.", parent=win)
                return
            if not self.printer_manager:
                messagebox.showerror("Impresora", "Sistema de impresión no disponible.", parent=win)
                return
            if not self.impresora_conectada:
                if not self.printer_manager.conectar_impresora():
                    messagebox.showerror("Impresora", "No se pudo conectar la impresora.", parent=win)
                    return
                self.impresora_conectada = True
            try:
                self.printer_manager.imprimir_factura(d)
                messagebox.showinfo("Imprimir", "Factura enviada a la impresora.", parent=win)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo imprimir:\n{e}", parent=win)

        btn_ver.config(command=abrir_ver_factura)
        btn_imp.config(command=imprimir_seleccionada)

        def _ymd_activo():
            return st["label_to_ymd"].get(vdia.get() or "", hoy_ymd)

        def _refrescar_fechas(todo7):
            fechas = set()
            for r in todo7:
                y = _venta_fecha_a_ymd(r[1])
                if y:
                    fechas.add(y)
            fechas.add(hoy_ymd)
            ymds = sorted(fechas, reverse=True)
            labels = [_etiqueta_dia_combo(y) for y in ymds]
            st["label_to_ymd"] = {lb: y for lb, y in zip(labels, ymds)}
            cb_dia["values"] = labels
            if hoy_ymd in ymds:
                vdia.set(_etiqueta_dia_combo(hoy_ymd))
            elif labels:
                vdia.set(labels[0])
            else:
                vdia.set("")

        def _fila_muestra_ymd(r, ymd):
            return _venta_fecha_a_ymd(r[1]) == ymd

        def __sel(_e):
            s = tree.selection()
            if not s:
                txt.config(state=tk.NORMAL)
                txt.delete("1.0", tk.END)
                txt.config(state=tk.DISABLED)
                return
            iid = s[0]
            if not str(iid).startswith("v"):
                txt.config(state=tk.NORMAL)
                txt.delete("1.0", tk.END)
                txt.config(state=tk.DISABLED)
                return
            vid = int(str(iid)[1:])
            txt.config(state=tk.NORMAL)
            txt.delete("1.0", tk.END)
            txt.insert(tk.END, self._texto_detalle_factura_por_id(vid))
            txt.config(state=tk.DISABLED)

        def _llenar_tabla():
            ymd = _ymd_activo()
            tree.delete(*tree.get_children())
            if not ymd:
                lbl_tit.config(text="Elija un día en la lista.")
                txt.config(state=tk.NORMAL)
                txt.delete("1.0", tk.END)
                txt.config(state=tk.DISABLED)
                return
            if not st["todo"]:
                lbl_tit.config(text="No hay ventas (prueba quitar el filtro de documento o elige otro día).")
                txt.config(state=tk.NORMAL)
                txt.delete("1.0", tk.END)
                txt.config(state=tk.DISABLED)
                return
            rows = [r for r in st["todo"] if _fila_muestra_ymd(r, ymd)]
            try:
                d0 = datetime.strptime(ymd, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                d0 = None
            if d0:
                lbl_tit.config(
                    text=f"Listado: {_DIAS_SEMANA[d0.weekday()]} {d0.day} de {_MESES[d0.month - 1]} {d0.year}  ·  {len(rows)} venta(s)"
                )
            else:
                lbl_tit.config(text=f"Día: {ymd}  ·  {len(rows)} venta(s)")
            rows.sort(key=lambda r: str(r[2] or ""), reverse=True)
            for r in rows:
                idv, fev, hora, doc, tot, _tip, nombre = r
                doc_s = (str(doc) if doc is not None else "").strip() or "—"
                fshort = (str(fev)[:10] if fev else "—")
                if len(fshort) == 10 and "-" in fshort:
                    try:
                        p = fshort.split("-")
                        fshort = f"{p[2]}/{p[1]}/{p[0]}"
                    except (IndexError, ValueError):
                        pass
                try:
                    tv = float(tot or 0)
                except (TypeError, ValueError):
                    tv = 0.0
                tree.insert(
                    "",
                    tk.END,
                    iid="v" + str(idv),
                    values=(f"#{idv}", (nombre or "—")[:80], doc_s, self.formato_peso(tv), (str(hora) or "—")[:12], fshort),
                )
            if not rows and ymd:
                tree.insert(
                    "", tk.END, iid="info_sin",
                    values=("—", "Sin ventas en este día" + (" (hoy)" if ymd == hoy_ymd else ""), "—", "—", "—", "—"),
                )
            ch = tree.get_children()
            if ch and str(ch[0]).startswith("v"):
                tree.selection_set(ch[0])
                tree.focus(ch[0])
                __sel(None)
            else:
                txt.config(state=tk.NORMAL)
                txt.delete("1.0", tk.END)
                txt.config(state=tk.DISABLED)

        def recargar():
            todo, err = self._ventas_cargar_enriquecido(vdoc.get().strip())
            if err:
                messagebox.showerror("Error", f"No se pudo leer las ventas: {err}", parent=win)
                st["todo"] = []
            else:
                st["todo"] = todo or []
            _refrescar_fechas(st["todo"])
            _llenar_tabla()

        def ir_hoy():
            for lb, y in st["label_to_ymd"].items():
                if y == hoy_ymd:
                    vdia.set(lb)
                    _llenar_tabla()
                    return
            _refrescar_fechas(st["todo"])
            if vdia.get():
                _llenar_tabla()

        def _camb_dia(_e=None):
            _llenar_tabla()

        btn_hoy.config(command=ir_hoy)
        btn_f.config(command=recargar)
        ent_doc.bind("<Return>", lambda e: recargar())
        tree.bind("<<TreeviewSelect>>", __sel)
        cb_dia.bind("<<ComboboxSelected>>", _camb_dia)
        recargar()

    def _inventario_por_clave(self, clave: str):
        """Localiza fila de inventario por código interno o por referencia (servicios)."""
        k = (clave or "").strip().lower()
        if not k:
            return None
        for p in self.productos_inventario:
            cod = str(p[0]).strip()
            ref = (p[5] if len(p) > 5 else "") or ""
            ref = str(ref).strip()
            if k == cod.lower() or k == cod.zfill(5).lower():
                return p
            if ref and k == ref.lower():
                return p
        return None

    def agregar_producto(self, codigo, nombre, precio):
        """Agregar producto o servicio de inventario al carrito; servicios no limitan por stock."""
        LIM = 9_999_999
        # Verificar stock disponible
        stock_disponible = 0
        es_servicio = False
        for p in self.productos_inventario:
            if str(p[0]) == str(codigo) or str(p[0]).zfill(5) == str(codigo).zfill(5):
                stock_disponible = int(p[2] or 0) if p[2] is not None else 0
                if len(p) >= 5 and (p[4] or "producto").lower() == "servicio":
                    es_servicio = True
                    stock_disponible = LIM
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
            # Verificar que hay stock para el primer producto (los servicios no se bloquean)
            if not es_servicio and stock_disponible <= 0:
                messagebox.showwarning("Sin stock", f"El producto '{nombre}' no tiene stock disponible")
                return
            
            # Agregar nuevo producto
            self.tabla.insert("", tk.END, values=(nombre, self.formato_peso(precio), 1, 
                                                 self.formato_peso(precio)))
            self.total_general.set(self.total_general.get() + precio)
            
            print(f"DEBUG: Nuevo producto agregado: {nombre}")
        
        self.actualizar_total()

    def escanear_codigo(self):
        """Acepta código interno, código de 5 cifras o referencia de servicio."""
        clave = self.codigo_entrada.get().strip()
        if not clave:
            return
        producto = self._inventario_por_clave(clave)
        if producto:
            es_srv = len(producto) >= 5 and (producto[4] or "producto").lower() == "servicio"
            if es_srv or (producto[2] is not None and int(producto[2]) > 0):
                self.agregar_producto(producto[0], producto[1], producto[3])
                self.scan_info.set(
                    f"Escaneado: {producto[1]}  ·  Precio: {self.formato_peso(float(producto[3] or 0))}"
                )
                self.codigo_entrada.set("")
                self.entry_codigo.focus()
                return
            self.scan_info.set(f"Sin stock: {producto[1]}")
        messagebox.showerror("No encontrado", "Producto no existe o sin stock")
        self.scan_info.set("Código no encontrado o sin stock")
        self.codigo_entrada.set("")

    def eliminar_seleccionado(self):
        """Elimina el producto seleccionado del carrito"""
        item = self.tabla.focus()
        if item:
            valores = self.tabla.item(item)["values"]
            self.total_general.set(self.total_general.get() - self.limpiar_precio(valores[3]))
            self.tabla.delete(item)
            self.actualizar_total()

    def pagar(self):
        """Elegir contado o fiado; el contado abre el cobro en efectivo."""
        if not self.documento.get().strip() or self.total_general.get() <= 0:
            messagebox.showerror("Error", "Ingresa documento y agrega productos")
            return
        total = self.total_general.get()
        doc = self.documento.get().strip()
        ventana = tk.Toplevel(self._toplevel)
        ventana.title("Tipo de pago")
        ventana.configure(bg=T.POS_BG)
        ventana.grab_set()
        centrar_ventana(ventana, 420, 220, self._toplevel)
        tk.Label(
            ventana,
            text="¿Cómo registra esta venta?",
            font=F_SUB,
            bg=T.POS_BG,
            fg=T.POS_TEXT,
        ).pack(pady=10)
        tk.Label(ventana, text=f"Total: {self.formato_peso(total)}", font=F_BODY_B, bg=T.POS_BG, fg=T.POS_MUTED).pack()
        tip = tk.StringVar(value="contado")
        tk.Radiobutton(
            ventana,
            text="Contado (efectivo ahora)",
            variable=tip,
            value="contado",
            bg=T.POS_BG,
            fg=T.POS_TEXT,
            font=F_BODY,
        ).pack(anchor="w", padx=40, pady=4)
        tk.Radiobutton(
            ventana,
            text="Fiado (cargo a cuenta; cobro en módulo Fiados)",
            variable=tip,
            value="fiado",
            bg=T.POS_BG,
            fg=T.POS_TEXT,
            font=F_BODY,
        ).pack(anchor="w", padx=40, pady=4)

        def siguiente():
            ventana.destroy()
            if tip.get() == "fiado":
                if messagebox.askyesno(
                    "Confirmar fiado",
                    f"Se cargará {self.formato_peso(total)} a la cuenta del documento {doc}.\n"
                    "El cliente podrá abonar o pagar luego en Fiados.\n\n¿Confirmar?",
                ):
                    self.procesar_venta_fiado()
            else:
                self._pagar_contado_ventana()

        tk.Button(
            ventana,
            text="Continuar",
            command=siguiente,
            bg=T.POS_BTN_GO,
            fg=T.WHITE,
            font=F_BODY_B,
            padx=20,
            pady=8,
            relief="flat",
            cursor="hand2",
        ).pack(pady=16)

    def _pagar_contado_ventana(self):
        """Ventana de efectivo (venta al contado)."""
        if not self.documento.get().strip() or self.total_general.get() <= 0:
            messagebox.showerror("Error", "Ingresa documento y agrega productos")
            return
        ventana = tk.Toplevel(self._toplevel)
        ventana.title("Cobro en efectivo")
        ventana.configure(bg=T.POS_BG)
        ventana.grab_set()
        centrar_ventana(ventana, 400, 250, self._toplevel)
        tk.Label(ventana, text="Cobro", font=F_SUB, bg=T.POS_BG, fg=T.POS_TEXT).pack(pady=12)
        tk.Label(ventana, text="Total", font=F_BODY_B, bg=T.POS_BG, fg=T.POS_MUTED).pack(pady=4)
        tk.Label(ventana, text=self.formato_peso(self.total_general.get()), font=(FONT, 14, "bold"), bg=T.POS_BG, fg=T.POS_TEXT).pack(pady=4)
        tk.Label(ventana, text="Efectivo recibido", font=F_BODY_B, bg=T.POS_BG, fg=T.POS_MUTED).pack(pady=(8, 4))
        efectivo = tk.StringVar(value="")
        entry = tk.Entry(ventana, textvariable=efectivo, font=F_BODY, width=20)
        entry.pack(pady=5)
        entry.focus()

        def completar():
            try:
                raw = (efectivo.get() or "").strip().replace(",", ".")
                if not raw:
                    messagebox.showerror("Error", "Ingresa el efectivo recibido")
                    return
                recibido = float(raw)
                total = self.total_general.get()
                if recibido >= total:
                    self.procesar_venta_completa(recibido, total)
                    ventana.destroy()
                else:
                    messagebox.showwarning("Efectivo insuficiente", "Monto recibido menor al total")
            except (tk.TclError, ValueError):
                messagebox.showerror("Error", "Ingresa un monto válido")

        entry.bind("<Return>", lambda e: completar())
        tk.Button(
            ventana,
            text="Completar pago",
            command=completar,
            bg=T.POS_BTN_GO,
            fg=T.WHITE,
            font=F_BODY_B,
            padx=20,
            pady=10,
            relief="flat",
            cursor="hand2",
        ).pack(pady=20)

    def procesar_venta_completa(self, recibido, total):
        """Procesa la venta y guarda en la base de datos (contado)."""
        try:
            datos_venta = {
                'factura': self.factura_num,
                'fecha': datetime.now().strftime('%d-%m-%Y'),
                'hora': datetime.now().strftime('%H:%M:%S'),
                'cliente': self.documento.get(),
                'productos': [(v[0], self.limpiar_precio(v[1]), int(v[2])) for v in [self.tabla.item(i)["values"] for i in self.tabla.get_children()]],
                'total': total
            }
            id_venta = self.guardar_venta_db(self.documento.get(), total, "contado")
            if id_venta:
                detalles = []
                for nombre_producto, precio, cantidad in datos_venta['productos']:
                    # BUSCAR EL CÓDIGO REAL DEL PRODUCTO POR SU NOMBRE
                    codigo_real = None
                    for row in self.productos_inventario:
                        codigo_inv, nombre_inv = row[0], row[1]
                        if nombre_inv == nombre_producto:
                            codigo_real = codigo_inv
                            break

                    if codigo_real is None:
                        print(f"⚠️ Advertencia: No se encontró código para '{nombre_producto}'")
                        codigo_real = "N/A"

                    subtotal = cantidad * precio
                    detalles.append((codigo_real, nombre_producto, precio, cantidad, subtotal))

                if self.guardar_detalle_ventas_db(id_venta, detalles):
                    if self.printer_manager and self.impresora_conectada:
                        self.printer_manager.imprimir_factura(datos_venta)
                        self.printer_manager.abrir_caja_registradora()
                    vuelto = recibido - total
                    messagebox.showinfo("✅ Pago Completado", f"💖 VENTA COMPLETADA 💖\n🧾 Factura: {self.factura_num}\n💸 Total: {self.formato_peso(total)}\n💵 Recibido: {self.formato_peso(recibido)}\n💰 Cambio: {self.formato_peso(vuelto)}\n🌸 ¡Gracias! 🌸")
                    self.limpiar_formulario()
                    self.productos_inventario = self.obtener_productos()
        except Exception as e:
            messagebox.showerror("Error", f"Error procesando venta: {e}")

    def procesar_venta_fiado(self):
        """Venta a fiado: registra deuda sin descontar stock; inventario al saldar en Fiados."""
        try:
            total = self.total_general.get()
            datos_venta = {
                'factura': self.factura_num,
                'fecha': datetime.now().strftime('%d-%m-%Y'),
                'hora': datetime.now().strftime('%H:%M:%S'),
                'cliente': self.documento.get(),
                'productos': [(v[0], self.limpiar_precio(v[1]), int(v[2])) for v in [self.tabla.item(i)["values"] for i in self.tabla.get_children()]],
                'total': total,
            }
            id_venta = self.guardar_venta_db(self.documento.get(), total, "fiado")
            if not id_venta:
                return
            detalles = []
            for nombre_producto, precio, cantidad in datos_venta['productos']:
                codigo_real = None
                for row in self.productos_inventario:
                    codigo_inv, nombre_inv = row[0], row[1]
                    if nombre_inv == nombre_producto:
                        codigo_real = codigo_inv
                        break
                if codigo_real is None:
                    print(f"⚠️ Advertencia: No se encontró código para '{nombre_producto}'")
                    codigo_real = "N/A"
                subtotal = cantidad * precio
                detalles.append((codigo_real, nombre_producto, precio, cantidad, subtotal))
            if self.guardar_detalle_ventas_db(id_venta, detalles, aplicar_stock=False):
                if self.printer_manager and self.impresora_conectada:
                    try:
                        self.printer_manager.imprimir_factura(datos_venta)
                    except Exception:
                        pass
                try:
                    upsert_cliente_por_cedula((self.documento.get() or "").strip(), None)
                except Exception as ex_f:
                    print(f"VmPOS: ficha cliente fiado (no crítico): {ex_f}")
                messagebox.showinfo(
                    "Fiado registrado",
                    f"📝 Venta a FIADO registrada\n🧾 Ref: {self.factura_num}\n"
                    f"Documento: {self.documento.get()}\n💳 Total a cuenta: {self.formato_peso(total)}\n\n"
                    "Cobra en: Módulo Fiados (menú principal).",
                )
                self.limpiar_formulario()
                self.productos_inventario = self.obtener_productos()
        except Exception as e:
            messagebox.showerror("Error", f"Error procesando fiado: {e}")
    def guardar_detalle_ventas_db(self, id_venta, productos_vendidos, aplicar_stock=True):
        """Guarda el detalle de la venta. Si aplicar_stock es False (fiado), no descuenta inventario."""
        try:
            with sqlite3.connect(ventas_db_path()) as conn:
                cursor = conn.cursor()
                cursor.execute("CREATE TABLE IF NOT EXISTS detalle_ventas (id INTEGER PRIMARY KEY AUTOINCREMENT, id_venta INTEGER, codigo_producto TEXT, nombre_producto TEXT, precio_unitario REAL, cantidad INTEGER, subtotal REAL)")
            
                for codigo, nombre, precio, cantidad, subtotal in productos_vendidos:
                    cursor.execute("INSERT INTO detalle_ventas (id_venta, codigo_producto, nombre_producto, precio_unitario, cantidad, subtotal) VALUES (?, ?, ?, ?, ?, ?)",
                              (id_venta, codigo, nombre, precio, cantidad, subtotal))
                    
                    if aplicar_stock and codigo != "N/A":
                        try:
                            cursor.execute(
                                "SELECT COALESCE(tipo, 'producto') FROM productos WHERE codigo = ?",
                                (codigo,),
                            )
                            tr = cursor.fetchone()
                        except sqlite3.OperationalError:
                            tr = None
                        t_item = (tr[0] or "producto").lower() if tr else "producto"
                        if t_item == "servicio":
                            continue
                        print(f"📦 Descontando {cantidad} unidades del producto {codigo}")
                        cursor.execute("UPDATE productos SET stock = stock - ? WHERE codigo = ?", (cantidad, codigo))
                    
                        # VERIFICAR QUE SE ACTUALIZÓ
                        cursor.execute("SELECT stock FROM productos WHERE codigo = ?", (codigo,))
                        nuevo_stock = cursor.fetchone()
                        if nuevo_stock:
                            print(f"✅ Nuevo stock para {codigo}: {nuevo_stock[0]}")
                        else:
                            print(f"⚠️ No se encontró producto con código {codigo} para actualizar stock")
                conn.commit()
            return True
        except Exception as e:
            messagebox.showerror("Error DB", f"Error guardando detalle: {e}")
            return False

    def guardar_venta_db(self, documento_cliente, total_venta, tipo_pago="contado"):
        """Guarda la venta y una fila en registro_clientes (histórico por cédula). Retorna el id de la venta."""
        try:
            with sqlite3.connect(ventas_db_path()) as conn:
                cursor = conn.cursor()
                ensure_fiado_schema(conn)
                cursor.execute(
                    "CREATE TABLE IF NOT EXISTS ventas (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "fecha_venta TEXT, hora_venta TEXT, documento_cliente TEXT, total_venta REAL)"
                )
                cursor.execute(
                    "INSERT INTO ventas (fecha_venta, hora_venta, documento_cliente, total_venta, tipo_pago) VALUES (?, ?, ?, ?, ?)",
                    (
                        datetime.now().strftime("%Y-%m-%d"),
                        datetime.now().strftime("%H:%M:%S"),
                        documento_cliente,
                        total_venta,
                        tipo_pago,
                    ),
                )
                id_venta = cursor.lastrowid
                if (tipo_pago or "").strip().lower() == "fiado":
                    try:
                        cursor.execute(
                            "UPDATE ventas SET stock_aplicado = 0 WHERE id = ?",
                            (id_venta,),
                        )
                    except sqlite3.OperationalError:
                        pass
                conn.commit()

                try:
                    cursor.execute("ALTER TABLE registro_clientes ADD COLUMN hora_compra TEXT")
                except Exception:
                    pass
                try:
                    cursor.execute("ALTER TABLE registro_clientes ADD COLUMN tipo_pago TEXT")
                except Exception:
                    pass
                try:
                    cursor.execute("ALTER TABLE registro_clientes ADD COLUMN id_venta INTEGER")
                except Exception:
                    pass
                fecha_actual = datetime.now().strftime("%Y-%m-%d")
                hora_actual = datetime.now().strftime("%H:%M:%S")
                cursor.execute(
                    "INSERT INTO registro_clientes (documento, fecha_compra, hora_compra, total_compras, tipo_pago, id_venta) VALUES (?, ?, ?, ?, ?, ?)",
                    (documento_cliente, fecha_actual, hora_actual, total_venta, tipo_pago, id_venta),
                )
                conn.commit()
                return id_venta
        except Exception as e:
            messagebox.showerror("Error DB", f"Error guardando venta: {e}")
            return None

    def limpiar_formulario(self):
        """Limpia el formulario para una nueva venta"""
        self.documento.set("")
        self.codigo_entrada.set("")
        self.total_general.set(0.0)
        self.factura_num = datetime.now().strftime("%Y%m%d%H%M%S")
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        self.actualizar_total()
        self.lbl_factura.config(text=f"🧾 Factura: {self.factura_num}")
        self.entry_doc.focus()

if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    root.mainloop()