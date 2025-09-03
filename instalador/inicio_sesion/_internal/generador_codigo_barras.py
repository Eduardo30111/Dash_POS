import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import datetime  # Agregar esta importación
from PIL import Image, ImageDraw, ImageFont
import io
import base64


# Importación condicional de PIL con manejo de errores
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_DISPONIBLE = True
except ImportError as e:
    print(f"Warning: PIL/Pillow no disponible: {e}")
    PIL_DISPONIBLE = False

class GeneradorCodigoBarras:
    """
    Generador de códigos de barras integrado al sistema VmPOS
    """
    def imprimir_codigo(self):
        """Envía el código de barras generado a la impresora POS"""
        if self.codigo_generado:
            messagebox.showinfo("🖨️ Imprimir", "Función de impresión aún no implementada.")
        else:
            messagebox.showwarning("⚠️ Sin código", "Primero debes generar un código de barras.")

    def __init__(self, parent=None):
        self.ventana = tk.Toplevel(parent) if parent else tk.Tk()
        self.codigo_generado = None
        self.setup_window()
        self.create_widgets()
        
    def setup_window(self):
        """Configura la ventana principal del generador"""
        self.ventana.title("🔢 Generador de Códigos de Barras - VmPOS")
        self.ventana.geometry("900x700")
        self.ventana.configure(bg="#ffeaa7")
        self.ventana.resizable(True, False)
        
        # Centrar ventana
        self.ventana.update_idletasks()
        x = (self.ventana.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.ventana.winfo_screenheight() // 2) - (700 // 2)
        self.ventana.geometry(f"900x700+{x}+{y}")
        
        # Hacer la ventana modal si tiene padre
        if self.ventana.master:
            self.ventana.transient(self.ventana.master)
            self.ventana.grab_set()
    
    def create_widgets(self):
        """Crea todos los widgets de la interfaz"""
        self.create_header()
        self.create_input_section()
        self.create_preview_section()
        self.create_buttons_section()
        self.create_footer()
    
    def create_header(self):
        """Crea el encabezado de la aplicación"""
        header_frame = tk.Frame(self.ventana, bg="#e84393", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        # Logo y título
        title_frame = tk.Frame(header_frame, bg="#e84393")
        title_frame.pack(expand=True)
        
        tk.Label(title_frame, text="🔢", font=("Segoe UI Emoji", 32), 
                bg="#e84393", fg="white").pack(side="left", padx=(0, 10), pady=15)
        
        tk.Label(title_frame, text="Generador de Códigos de Barras", 
                font=("Segoe UI", 20, "bold"), bg="#e84393", fg="white").pack(side="left", pady=20)
    
    def create_input_section(self):
        """Crea la sección de entrada de datos"""
        input_frame = tk.LabelFrame(self.ventana, text="📝 Configuración del Código", 
                                   bg="#ffeaa7", fg="#2d3436", font=("Segoe UI", 12, "bold"),
                                   bd=2, relief="solid")
        input_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        # Frame para organizar en grid
        grid_frame = tk.Frame(input_frame, bg="#ffeaa7")
        grid_frame.pack(fill="x", padx=20, pady=15)
        
        # Entrada de texto/número
        tk.Label(grid_frame, text="Número o Texto:", font=("Segoe UI", 11, "bold"), 
                bg="#ffeaa7", fg="#2d3436").grid(row=0, column=0, sticky="w", pady=5)
        
        self.entry_codigo = tk.Entry(grid_frame, font=("Segoe UI", 12), width=30, 
                                    bd=2, relief="solid")
        self.entry_codigo.grid(row=0, column=1, padx=(10, 0), pady=5, sticky="ew")
        self.entry_codigo.bind('<KeyRelease>', self.on_text_change)
        
        # Selector de formato
        tk.Label(grid_frame, text="Formato:", font=("Segoe UI", 11, "bold"), 
                bg="#ffeaa7", fg="#2d3436").grid(row=1, column=0, sticky="w", pady=5)
        
        self.combo_formato = ttk.Combobox(grid_frame, font=("Segoe UI", 11), width=28, state="readonly")
        self.combo_formato.grid(row=1, column=1, padx=(10, 0), pady=5, sticky="ew")
        
        # Opciones de formato
        self.formatos = {
            "CODE128": "CODE128 (Recomendado - Alfanumérico)",
            "CODE39": "CODE39 (Números y letras mayúsculas)",
            "EAN13": "EAN13 (Productos comerciales - 13 dígitos)",
            "EAN8": "EAN8 (Productos pequeños - 8 dígitos)",
            "UPC-A": "UPC-A (Estándar USA - 12 dígitos)",
            "ITF": "ITF-14 (Logística - dígitos pares)"
        }
        
        self.combo_formato['values'] = list(self.formatos.values())
        self.combo_formato.set(self.formatos["CODE128"])
        self.combo_formato.bind('<<ComboboxSelected>>', self.on_format_change)
        
        # Configurar grid
        grid_frame.columnconfigure(1, weight=1)
        
        # Frame para opciones adicionales
        opciones_frame = tk.Frame(input_frame, bg="#ffeaa7")
        opciones_frame.pack(fill="x", padx=20, pady=10)
        
        # Checkboxes para opciones
        self.mostrar_texto = tk.BooleanVar(value=True)
        tk.Checkbutton(opciones_frame, text="Mostrar texto debajo del código", 
                      variable=self.mostrar_texto, bg="#ffeaa7", font=("Segoe UI", 10)).pack(anchor="w")
        
        self.incluir_checksum = tk.BooleanVar(value=True)
        tk.Checkbutton(opciones_frame, text="Incluir dígito de control (checksum)", 
                      variable=self.incluir_checksum, bg="#ffeaa7", font=("Segoe UI", 10)).pack(anchor="w")
    
    def create_preview_section(self):
        """Crea la sección de vista previa"""
        preview_frame = tk.LabelFrame(self.ventana, text="👁️ Vista Previa", 
                                     bg="#ffeaa7", fg="#2d3436", font=("Segoe UI", 12, "bold"),
                                     bd=2, relief="solid")
        preview_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Canvas para mostrar el código de barras
        canvas_frame = tk.Frame(preview_frame, bg="white", bd=2, relief="solid")
        canvas_frame.pack(fill="both", expand=True, padx=20, pady=15)
        
        self.canvas = tk.Canvas(canvas_frame, bg="white", height=200)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Mensaje inicial
        self.canvas.create_text(self.canvas.winfo_reqwidth()//2, 100, 
                               text="Ingresa un código para generar la vista previa", 
                               font=("Segoe UI", 12), fill="#636e72", tags="mensaje")
        
        # Información del código
        info_frame = tk.Frame(preview_frame, bg="#ffeaa7")
        info_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.lbl_info = tk.Label(info_frame, text="", font=("Segoe UI", 10), 
                                bg="#ffeaa7", fg="#636e72")
        self.lbl_info.pack()
    
    def create_buttons_section(self):
        """Crea la sección de botones"""
        buttons_frame = tk.Frame(self.ventana, bg="#ffeaa7")
        buttons_frame.pack(fill="x", padx=20, pady=10)
        
        # Botón generar
        self.btn_generar = tk.Button(buttons_frame, text="✨ Generar Código", 
                                    font=("Segoe UI", 12, "bold"), bg="#00b894", fg="white",
                                    bd=0, pady=12, cursor="hand2", relief="flat",
                                    command=self.generar_codigo)
        self.btn_generar.pack(side="left", padx=(0, 10), ipadx=20)
        
        # Botón guardar
        self.btn_guardar = tk.Button(buttons_frame, text="💾 Guardar PNG", 
                                    font=("Segoe UI", 12, "bold"), bg="#0984e3", fg="white",
                                    bd=0, pady=12, cursor="hand2", relief="flat",
                                    command=self.guardar_codigo, state="disabled")
        self.btn_guardar.pack(side="left", padx=5, ipadx=20)
        
        # Botón imprimir
        self.btn_imprimir = tk.Button(buttons_frame, text="🖨️ Imprimir", 
                                     font=("Segoe UI", 12, "bold"), bg="#fdcb6e", fg="white",
                                     bd=0, pady=12, cursor="hand2", relief="flat",
                                     command=self.imprimir_codigo, state="disabled")
        self.btn_imprimir.pack(side="left", padx=5, ipadx=20)
        
        # Botón limpiar
        self.btn_limpiar = tk.Button(buttons_frame, text="🗑️ Limpiar", 
                                    font=("Segoe UI", 12, "bold"), bg="#636e72", fg="white",
                                    bd=0, pady=12, cursor="hand2", relief="flat",
                                    command=self.limpiar_todo)
        self.btn_limpiar.pack(side="left", padx=5, ipadx=20)
        
        # Botón cerrar
        self.btn_cerrar = tk.Button(buttons_frame, text="❌ Cerrar", 
                                   font=("Segoe UI", 12, "bold"), bg="#e17055", fg="white",
                                   bd=0, pady=12, cursor="hand2", relief="flat",
                                   command=self.cerrar_ventana)
        self.btn_cerrar.pack(side="right", ipadx=20)
    
    def create_footer(self):
        """Crea el pie de página"""
        footer_frame = tk.Frame(self.ventana, bg="#e84393", height=40)
        footer_frame.pack(fill="x")
        footer_frame.pack_propagate(False)
        
        tk.Label(footer_frame, text="💫 VmPOS - Generador de Códigos de Barras v1.0", 
                font=("Segoe UI", 10, "bold"), bg="#e84393", fg="white").pack(pady=10)
    
    def on_text_change(self, event=None):
        """Maneja el cambio en el texto de entrada"""
        if self.entry_codigo.get().strip():
            self.btn_generar.config(state="normal")
        else:
            self.btn_generar.config(state="disabled")
            self.limpiar_canvas()
    
    def on_format_change(self, event=None):
        """Maneja el cambio de formato"""
        if self.entry_codigo.get().strip():
            self.generar_codigo()
    
    def get_selected_format(self):
        """Obtiene el formato seleccionado"""
        formato_texto = self.combo_formato.get()
        for codigo, texto in self.formatos.items():
            if texto == formato_texto:
                return codigo
        return "CODE128"
    
    def validar_entrada(self, texto, formato):
        """Valida la entrada según el formato seleccionado"""
        if not texto:
            return False, "El texto no puede estar vacío"
        
        if formato == "EAN13":
            if not texto.isdigit() or len(texto) not in [12, 13]:
                return False, "EAN13 requiere 12 o 13 dígitos"
        elif formato == "EAN8":
            if not texto.isdigit() or len(texto) not in [7, 8]:
                return False, "EAN8 requiere 7 u 8 dígitos"
        elif formato == "UPC-A":
            if not texto.isdigit() or len(texto) not in [11, 12]:
                return False, "UPC-A requiere 11 o 12 dígitos"
        elif formato == "ITF":
            if not texto.isdigit() or len(texto) % 2 != 0:
                return False, "ITF requiere un número par de dígitos"
        elif formato == "CODE39":
            caracteres_validos = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-. $/+%"
            if not all(c in caracteres_validos for c in texto.upper()):
                return False, "CODE39 solo acepta números, letras mayúsculas y: -. $/+%"
        
        return True, "Válido"
    
    def dibujar_florecita(self, draw, x, y, tamaño=12, color='#ff7675'):
        """Dibuja una florecita decorativa con mejor resolución"""
        # Pétalos (círculos pequeños alrededor del centro)
        petalos_pos = [
            (x, y-tamaño//2),      # arriba
            (x+tamaño//2, y),      # derecha
            (x, y+tamaño//2),      # abajo
            (x-tamaño//2, y),      # izquierda
            (x-tamaño//3, y-tamaño//3),  # diagonal sup izq
            (x+tamaño//3, y-tamaño//3),  # diagonal sup der
            (x+tamaño//3, y+tamaño//3),  # diagonal inf der
            (x-tamaño//3, y+tamaño//3),  # diagonal inf izq
        ]
        
        # Dibujar pétalos más grandes
        petal_size = tamaño // 4
        for px, py in petalos_pos:
            draw.ellipse([px-petal_size, py-petal_size, px+petal_size, py+petal_size], fill=color)
        
        # Centro de la flor más grande
        center_size = tamaño // 3
        draw.ellipse([x-center_size, y-center_size, x+center_size, y+center_size], fill='#fdcb6e')
    
    def generar_codigo_simple(self, texto, formato):
        """Genera un código de barras simple en formato etiqueta pequeña con alta resolución"""
        if not PIL_DISPONIBLE:
            messagebox.showerror("❌ Error", "PIL/Pillow no está disponible.\nInstale con: pip install Pillow")
            return None
            
        # Dimensiones para etiqueta pequeña con buena resolución
        width = 600  # Ancho con buena resolución
        height = 240  # Alto total con buena resolución
        barcode_height = 100  # Alto del código de barras
        
        # Crear imagen con fondo blanco y alta resolución
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        
        # Dibujar borde de la etiqueta
        draw.rectangle([4, 4, width-5, height-5], outline='#ddd', width=2)
        
        # === HEADER: "Variedades Marce" con florecitas ===
        try:
            # Cargar fuente más grande para mejor resolución
            font_titulo = ImageFont.truetype("arial.ttf", 24)
        except:
            try:
                font_titulo = ImageFont.truetype("Arial.ttf", 24)
            except:
                font_titulo = ImageFont.load_default()
        
        # Texto "Variedades Marce" centrado
        titulo = "Variedades Marce"
        try:
            text_bbox = draw.textbbox((0, 0), titulo, font=font_titulo)
            text_width = text_bbox[2] - text_bbox[0]
        except:
            text_width = len(titulo) * 14  # Estimación si textbbox no funciona
        
        text_x = (width - text_width) // 2
        text_y = 15
        
        # Dibujar el título centrado
        draw.text((text_x, text_y), titulo, fill='#2d3436', font=font_titulo)
        
        # Dibujar florecitas a los lados del título (mejor centradas)
        flor_y = text_y + 12  # Centrar verticalmente con el texto
        
        # Florecita izquierda
        flor_izq_x = text_x - 35
        self.dibujar_florecita(draw, flor_izq_x, flor_y, tamaño=12, color='#ff7675')
        
        # Florecita derecha
        flor_der_x = text_x + text_width + 25
        self.dibujar_florecita(draw, flor_der_x, flor_y, tamaño=12, color='#ff7675')
        
        # === CÓDIGO DE BARRAS CENTRADO ===
        barcode_start_y = 55
        bar_width = 3  # Barras más anchas para mejor resolución
        
        # Calcular el ancho total del código de barras
        total_bars = 0
        for char in texto:
            char_code = ord(char) % 10
            total_bars += char_code + 1
        
        barcode_width = total_bars * (bar_width + 1)
        start_x = (width - barcode_width) // 2  # Centrar el código de barras
        
        x = start_x
        # Generar patrón de barras centrado
        for i, char in enumerate(texto):
            char_code = ord(char) % 10
            for j in range(char_code + 1):
                if (i + j) % 2 == 0:
                    draw.rectangle([x, barcode_start_y, x + bar_width, 
                                  barcode_start_y + barcode_height], fill='black')
                x += bar_width + 1
                
                # Evitar que el código se salga del área
                if x > width - 30:
                    break
            if x > width - 30:
                break
        
        # === TEXTO DEBAJO DEL CÓDIGO CENTRADO ===
        if self.mostrar_texto.get():
            try:
                font_codigo = ImageFont.truetype("arial.ttf", 18)
            except:
                try:
                    font_codigo = ImageFont.truetype("Arial.ttf", 18)
                except:
                    font_codigo = ImageFont.load_default()
            
            # Centrar el texto del código
            try:
                codigo_bbox = draw.textbbox((0, 0), texto, font=font_codigo)
                codigo_width = codigo_bbox[2] - codigo_bbox[0]
            except:
                codigo_width = len(texto) * 10  # Estimación
            
            codigo_x = (width - codigo_width) // 2
            codigo_y = barcode_start_y + barcode_height + 15
            
            draw.text((codigo_x, codigo_y), texto, fill='#2d3436', font=font_codigo)
        
        return img
    
    def generar_codigo(self):
        """Genera el código de barras"""
        texto = self.entry_codigo.get().strip()
        formato = self.get_selected_format()
        
        if not texto:
            messagebox.showwarning("⚠️ Campo vacío", "Por favor ingresa un texto o número.")
            return
        
        # Validar entrada
        es_valido, mensaje = self.validar_entrada(texto, formato)
        if not es_valido:
            messagebox.showerror("❌ Error de validación", mensaje)
            return
        
        try:
            # Generar código de barras en formato etiqueta
            self.codigo_generado = self.generar_codigo_simple(texto, formato)
            
            # Mostrar en canvas
            self.mostrar_en_canvas(self.codigo_generado)
            
            # Actualizar información
            self.lbl_info.config(text=f"Etiqueta: {texto} | Formato: {formato} | Variedades Marce ✅")
            
            # Habilitar botones
            self.btn_guardar.config(state="normal")
            self.btn_imprimir.config(state="normal")
            
            messagebox.showinfo("✅ Éxito", "¡Etiqueta con código de barras generada exitosamente!")
            
        except Exception as e:
            messagebox.showerror("❌ Error", f"Error al generar código: {str(e)}")
    
    def mostrar_en_canvas(self, imagen):
        """Muestra la imagen del código de barras en el canvas"""
        if not imagen:
            return
            
        # Limpiar canvas
        self.canvas.delete("all")
        
        # Convertir PIL Image a PhotoImage
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = 400
            canvas_height = 200
        
        # Redimensionar imagen manteniendo aspecto para visualización (sin afectar calidad original)
        img_width, img_height = imagen.size
        ratio = min((canvas_width - 40) / img_width, (canvas_height - 40) / img_height)
        new_width = int(img_width * ratio)
        new_height = int(img_height * ratio)
        
        # Solo redimensionar para mostrar, pero mantener original para guardar
        imagen_para_mostrar = imagen.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Convertir a PhotoImage
        self.photo = tk.PhotoImage(data=self.pil_to_base64(imagen_para_mostrar))
        
        # Centrar en canvas
        x = canvas_width // 2
        y = canvas_height // 2
        self.canvas.create_image(x, y, image=self.photo, tags="barcode")
    
    def pil_to_base64(self, imagen):
        """Convierte imagen PIL a base64 para PhotoImage"""
        buffer = io.BytesIO()
        imagen.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return img_str
    
    def limpiar_canvas(self):
        """Limpia el canvas"""
        self.canvas.delete("all")
        self.canvas.create_text(self.canvas.winfo_width()//2, self.canvas.winfo_height()//2, 
                               text="Ingresa un código para generar la vista previa", 
                               font=("Segoe UI", 12), fill="#636e72", tags="mensaje")
    
    def guardar_codigo(self):
        """Guarda el código de barras como imagen PNG"""
        if not self.codigo_generado:
            messagebox.showwarning("⚠️ Sin código", "Primero debes generar un código de barras.")
            return

        # Obtener el directorio de descargas del usuario
        import os
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")

        # Crear nombre de archivo por defecto
        texto_codigo = self.entry_codigo.get().strip()
        formato = self.get_selected_format()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_default = f"codigo_barras_{texto_codigo}_{formato}_{timestamp}.png"

        # Diálogo para guardar archivo con opciones corregidas
        filename = filedialog.asksaveasfilename(
            title="Guardar código de barras",
            initialdir=downloads_path,
            initialfile=filename_default,
            defaultextension=".png",
            filetypes=[("Archivos PNG", "*.png"), ("Todos los archivos", "*.*")]
    )

        if filename:
           try:
                self.codigo_generado.save(filename)
                messagebox.showinfo("✅ Guardado", f"Código de barras guardado exitosamente en:\n{filename}")

                # Preguntar si quiere abrir la carpeta
                respuesta = messagebox.askyesno("📂 Abrir carpeta", "¿Deseas abrir la carpeta donde se guardó el archivo?")
                if respuesta:
                    import subprocess
                    import sys
                    if sys.platform.startswith('win'):
                        subprocess.Popen(['explorer', '/select,', filename])
                    elif sys.platform.startswith('darwin'):  # macOS
                        subprocess.Popen(['open', '-R', filename])
                    else:  # Linux
                        subprocess.Popen(['xdg-open', os.path.dirname(filename)])

           except Exception as e:
                messagebox.showerror("❌ Error", f"Error al guardar archivo:\n{str(e)}")

    
    def limpiar_todo(self):
        """Limpia todos los campos y reinicia la interfaz"""
        self.entry_codigo.delete(0, tk.END)
        self.combo_formato.set(self.formatos["CODE128"])
        self.mostrar_texto.set(True)
        self.incluir_checksum.set(True)
        self.limpiar_canvas()
        self.lbl_info.config(text="")
        
        # Deshabilitar botones
        self.btn_guardar.config(state="disabled")
        self.btn_imprimir.config(state="disabled")
        self.btn_generar.config(state="disabled")
        
        self.codigo_generado = None
    
    def cerrar_ventana(self):
        """Cierra la ventana del generador"""
        self.ventana.destroy()

def iniciar_generador_barras(parent=None):
    """Función para iniciar el generador de códigos de barras"""
    try:
        app = GeneradorCodigoBarras(parent)
        if not parent:  # Si no hay ventana padre, ejecutar mainloop
            app.ventana.mainloop()
        return app
    except Exception as e:
        if parent:
            messagebox.showerror("❌ Error", f"Error al iniciar generador de códigos de barras:\n{str(e)}")
        else:
            print(f"Error al iniciar generador: {e}")
        return None

if __name__ == "__main__":
    # Ejecutar como aplicación independiente
    iniciar_generador_barras()