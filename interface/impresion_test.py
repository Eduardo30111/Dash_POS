from escpos.printer import Usb, Win32Raw
import usb.core
import usb.util
import sys
import time

class PrinterManager:
    def __init__(self):
        self.printer = None
        self.printer_type = None
    
    def connect_usb_printer(self):
        """Intenta conectar con impresora USB con múltiples configuraciones"""
        
        # Configuraciones comunes para impresoras térmicas
        configs = [
            # Gprinter GP-58
            {"vid": 0x0416, "pid": 0x5011, "in_ep": 0x82, "out_ep": 0x01},
            {"vid": 0x0416, "pid": 0x5011, "in_ep": 0x81, "out_ep": 0x02},
            {"vid": 0x0416, "pid": 0x5011, "in_ep": 0x82, "out_ep": 0x02},
            
            # Configuraciones genéricas
            {"vid": 0x04b8, "pid": 0x0202, "in_ep": 0x82, "out_ep": 0x01},  # Epson
            {"vid": 0x04b8, "pid": 0x0005, "in_ep": 0x82, "out_ep": 0x01},  # Epson TM
        ]
        
        print("🔍 Buscando impresoras USB...")
        
        # Buscar dispositivos conectados
        devices = usb.core.find(find_all=True)
        available_printers = []
        
        for device in devices:
            try:
                # Verificar si es una impresora
                if device.bDeviceClass == 7 or any(config["vid"] == device.idVendor and config["pid"] == device.idProduct for config in configs):
                    available_printers.append((device.idVendor, device.idProduct))
                    print(f"📱 Impresora encontrada: VID={hex(device.idVendor)}, PID={hex(device.idProduct)}")
            except:
                continue
        
        if not available_printers:
            print("❌ No se encontraron impresoras USB")
            return False
        
        # Probar conexión con cada impresora encontrada
        for vid, pid in available_printers:
            print(f"\n🔌 Probando conexión con VID={hex(vid)}, PID={hex(pid)}")
            
            # Probar configuraciones específicas primero
            specific_configs = [config for config in configs if config["vid"] == vid and config["pid"] == pid]
            
            for config in specific_configs:
                if self._test_usb_config(config):
                    return True
            
            # Si no funciona, probar configuraciones genéricas
            generic_configs = [
                {"vid": vid, "pid": pid, "in_ep": 0x82, "out_ep": 0x01},
                {"vid": vid, "pid": pid, "in_ep": 0x81, "out_ep": 0x02},
                {"vid": vid, "pid": pid, "in_ep": 0x82, "out_ep": 0x02},
                {"vid": vid, "pid": pid, "in_ep": 0x83, "out_ep": 0x03},
            ]
            
            for config in generic_configs:
                if self._test_usb_config(config):
                    return True
        
        return False
    
    def _test_usb_config(self, config):
        """Prueba una configuración específica de USB"""
        try:
            printer = Usb(
                idVendor=config["vid"],
                idProduct=config["pid"],
                timeout=5000,
                in_ep=config["in_ep"],
                out_ep=config["out_ep"]
            )
            
            # Prueba simple
            printer.text("Test\n")
            
            self.printer = printer
            self.printer_type = "USB"
            print(f"✅ Conexión exitosa con endpoints: in={hex(config['in_ep'])}, out={hex(config['out_ep'])}")
            return True
            
        except Exception as e:
            print(f"❌ Error con configuración {config}: {str(e)[:50]}...")
            return False
    
    def connect_windows_printer(self, printer_name=None):
        """Conecta usando el driver de Windows"""
        try:
            if printer_name:
                printer = Win32Raw(printer_name)
            else:
                # Buscar impresoras instaladas en Windows
                import win32print
                printers = [printer[2] for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL)]
                
                if not printers:
                    print("❌ No se encontraron impresoras instaladas en Windows")
                    return False
                
                print("🖨️ Impresoras disponibles en Windows:")
                for i, p in enumerate(printers):
                    print(f"  {i+1}. {p}")
                
                # Usar la primera impresora disponible
                printer = Win32Raw(printers[0])
                print(f"📌 Usando impresora: {printers[0]}")
            
            self.printer = printer
            self.printer_type = "Windows"
            return True
            
        except Exception as e:
            print(f"❌ Error conectando impresora Windows: {e}")
            return False
    
    def print_test(self):
        """Imprime una página de prueba"""
        if not self.printer:
            print("❌ No hay impresora conectada")
            return False
        
        try:
            print("🖨️ Imprimiendo página de prueba...")
            
            self.printer.text("="*40 + "\n")
            self.printer.text("    PRUEBA DE IMPRESION\n")
            self.printer.text("="*40 + "\n")
            self.printer.text(f"Tipo de conexión: {self.printer_type}\n")
            self.printer.text(f"Fecha: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            self.printer.text("Estado: FUNCIONANDO\n")
            self.printer.text("="*40 + "\n")
            self.printer.text("\n\n")
            
            # Cortar papel si es posible
            try:
                self.printer.cut()
            except:
                pass
            
            print("✅ Impresión completada exitosamente")
            return True
            
        except Exception as e:
            print(f"❌ Error al imprimir: {e}")
            return False
    
    def close(self):
        """Cierra la conexión de la impresora"""
        if self.printer:
            try:
                self.printer.close()
                print("🔌 Conexión cerrada")
            except:
                pass

def main():
    print("🖨️ SISTEMA DE PRUEBA DE IMPRESIÓN")
    print("=" * 50)
    
    manager = PrinterManager()
    
    try:
        # Método 1: Intentar conexión USB
        print("\n📡 Método 1: Conexión USB directa")
        if manager.connect_usb_printer():
            if manager.print_test():
                print("\n🎉 ¡Impresión USB exitosa!")
            else:
                print("\n⚠️ Conexión USB ok, pero falló la impresión")
        else:
            print("\n❌ Conexión USB falló")
            
            # Método 2: Intentar conexión por Windows
            print("\n📡 Método 2: Conexión por driver de Windows")
            if manager.connect_windows_printer():
                if manager.print_test():
                    print("\n🎉 ¡Impresión por Windows exitosa!")
                else:
                    print("\n⚠️ Conexión Windows ok, pero falló la impresión")
            else:
                print("\n❌ Todas las conexiones fallaron")
                print("\n💡 Soluciones sugeridas:")
                print("1. Ejecutar como administrador")
                print("2. Verificar que la impresora esté encendida")
                print("3. Reinstalar el driver de la impresora")
                print("4. Probar con otro cable USB")
    
    except KeyboardInterrupt:
        print("\n👋 Prueba cancelada por el usuario")
    
    except Exception as e:
        print(f"\n💥 Error inesperado: {e}")
    
    finally:
        manager.close()

if __name__ == "__main__":
    main()