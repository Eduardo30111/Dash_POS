import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import datetime  # Agregar esta importación
import io
import base64

from ui_theme import T, F_TITLE, F_HEAD, F_BODY, F_BODY_B, F_SMALL


# Importación condicional de PIL con manejo de errores
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_DISPONIBLE = True
except ImportError as e:
    print(f"Warning: PIL/Pillow no disponible: {e}")
    PIL_DISPONIBLE = False

# Generación estándar de códigos de barras (legibles por lectores físicos)
try:
    import barcode
    from barcode.writer import ImageWriter
    BARCODE_LIB_DISPONIBLE = True
except ImportError as e:
    print(f"Warning: python-barcode no disponible: {e}")
    BARCODE_LIB_DISPONIBLE = False

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
        if self.ventana.master is not None:
            from navegacion_ventanas import instalar_barra_volver
            instalar_barra_volver(self.ventana, self.ventana.master)
        from layout_responsive import centrar_ventana, crear_cuerpo_modulo_scroll, modulo_scroll_finalizar

        self.ventana.title("Generador de códigos de barras · VmPOS")
        self.ventana.configure(bg=T.BG_APP)
        self.ventana.resizable(True, True)
        self.cuerpo = crear_cuerpo_modulo_scroll(self.ventana, bg=T.BG_APP)
        centrar_ventana(self.ventana, 900, 700, self.ventana.master if self.ventana.master else None)
        
        # Ventana hija del menú (sin grab global para permitir «Volver» limpio)
        if self.ventana.master:
            self.ventana.transient(self.ventana.master)
    
    def create_widgets(self):
        """Crea todos los widgets de la interfaz"""
        self.create_header()
        self.create_input_section()
        self.create_preview_section()
        self.create_buttons_section()
        self.create_footer()
        modulo_scroll_finalizar(self.cuerpo)
    
    def create_header(self):
        """Crea el encabezado de la aplicación"""
        header_frame = tk.Frame(self.cuerpo, bg=T.POS_HEADER, height=76)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)

        title_frame = tk.Frame(header_frame, bg=T.POS_HEADER)
        title_frame.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=(12, 14))

        tk.Label(title_frame, text="Códigos de barras", font=F_TITLE, bg=T.POS_HEADER, fg=T.WHITE).pack(anchor="w")
        tk.Label(
            title_frame,
            text="Elija formato, ingrese datos y genere imagen PNG para productos o etiquetas.",
            font=F_SMALL,
            bg=T.POS_HEADER,
            fg=T.HEADER_TEXT_DIM,
            wraplength=680,
            justify="left",
        ).pack(anchor="w", pady=(4, 0))
    
    def create_input_section(self):
        """Crea la sección de entrada de datos"""
        wrap = tk.Frame(self.cuerpo, bg=T.BG_APP)
        wrap.pack(fill="x", padx=16, pady=(16, 8))
        input_frame = tk.Frame(wrap, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
        input_frame.pack(fill="x")
        tk.Frame(input_frame, bg=T.STAT_2, height=3).pack(fill="x")
        tk.Label(input_frame, text="Configuración", font=F_HEAD, bg=T.BG_CARD, fg=T.TEXT).pack(anchor="w", padx=14, pady=(10, 6))

        grid_frame = tk.Frame(input_frame, bg=T.BG_CARD)
        grid_frame.pack(fill="x", padx=14, pady=(0, 12))

        tk.Label(grid_frame, text="Número o texto", font=F_BODY_B, bg=T.BG_CARD, fg=T.TEXT).grid(
            row=0, column=0, sticky="w", pady=5
        )

        self.entry_codigo = tk.Entry(
            grid_frame, font=F_BODY, width=30, relief="flat", bd=0,
            highlightthickness=1, highlightbackground=T.INPUT_BORDER,
        )
        self.entry_codigo.grid(row=0, column=1, padx=(10, 0), pady=5, sticky="ew", ipady=4)
        self.entry_codigo.bind("<KeyRelease>", self.on_text_change)

        tk.Label(grid_frame, text="Formato", font=F_BODY_B, bg=T.BG_CARD, fg=T.TEXT).grid(
            row=1, column=0, sticky="w", pady=5
        )
        
        self.combo_formato = ttk.Combobox(grid_frame, font=F_BODY, width=28, state="readonly")
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
        
        opciones_frame = tk.Frame(input_frame, bg=T.BG_CARD)
        opciones_frame.pack(fill="x", padx=14, pady=(0, 12))

        self.mostrar_texto = tk.BooleanVar(value=True)
        tk.Checkbutton(
            opciones_frame,
            text="Mostrar texto legible debajo del código",
            variable=self.mostrar_texto,
            bg=T.BG_CARD,
            fg=T.TEXT,
            font=F_BODY,
            activebackground=T.BG_CARD,
            activeforeground=T.TEXT,
            selectcolor=T.BG_CARD,
        ).pack(anchor="w")

        self.incluir_checksum = tk.BooleanVar(value=True)
        tk.Checkbutton(
            opciones_frame,
            text="Incluir dígito de control (checksum) cuando aplique",
            variable=self.incluir_checksum,
            bg=T.BG_CARD,
            fg=T.TEXT,
            font=F_BODY,
            activebackground=T.BG_CARD,
            activeforeground=T.TEXT,
            selectcolor=T.BG_CARD,
        ).pack(anchor="w")
    
    def create_preview_section(self):
        """Crea la sección de vista previa"""
        pwrap = tk.Frame(self.cuerpo, bg=T.BG_APP)
        pwrap.pack(fill="both", expand=True, padx=16, pady=8)
        preview_frame = tk.Frame(pwrap, bg=T.BG_CARD, highlightbackground=T.BORDER, highlightthickness=1)
        preview_frame.pack(fill="both", expand=True)
        tk.Frame(preview_frame, bg=T.STAT_1, height=3).pack(fill="x")
        tk.Label(preview_frame, text="Vista previa", font=F_HEAD, bg=T.BG_CARD, fg=T.TEXT).pack(anchor="w", padx=14, pady=(10, 6))

        canvas_frame = tk.Frame(preview_frame, bg=T.INPUT_BG_ALT, highlightbackground=T.BORDER, highlightthickness=1)
        canvas_frame.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        self.canvas = tk.Canvas(canvas_frame, bg=T.WHITE, height=200, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=8, pady=8)

        self.canvas.create_text(
            self.canvas.winfo_reqwidth() // 2,
            100,
            text="Ingrese un valor y pulse Generar para ver el código",
            font=F_BODY,
            fill=T.TEXT_MUTED,
            tags="mensaje",
        )

        info_frame = tk.Frame(preview_frame, bg=T.BG_CARD)
        info_frame.pack(fill="x", padx=14, pady=(0, 12))

        self.lbl_info = tk.Label(info_frame, text="", font=F_SMALL, bg=T.BG_CARD, fg=T.TEXT_MUTED)
        self.lbl_info.pack(anchor="w")
    
    def create_buttons_section(self):
        """Crea la sección de botones"""
        buttons_frame = tk.Frame(self.cuerpo, bg=T.BG_APP)
        buttons_frame.pack(fill="x", padx=16, pady=(0, 12))

        self.btn_generar = tk.Button(
            buttons_frame,
            text="Generar",
            font=F_BODY_B,
            bg=T.STAT_3,
            fg=T.WHITE,
            bd=0,
            pady=10,
            cursor="hand2",
            relief="flat",
            command=self.generar_codigo,
            activebackground=T.POS_BTN_GO_HOVER,
            activeforeground=T.WHITE,
        )
        self.btn_generar.pack(side="left", padx=(0, 8), ipadx=16)

        self.btn_guardar = tk.Button(
            buttons_frame,
            text="Guardar PNG",
            font=F_BODY_B,
            bg=T.STAT_1,
            fg=T.WHITE,
            bd=0,
            pady=10,
            cursor="hand2",
            relief="flat",
            command=self.guardar_codigo,
            state="disabled",
            activebackground="#0284c7",
            activeforeground=T.WHITE,
        )
        self.btn_guardar.pack(side="left", padx=6, ipadx=12)

        self.btn_imprimir = tk.Button(
            buttons_frame,
            text="Imprimir",
            font=F_BODY_B,
            bg=T.STAT_4,
            fg=T.WHITE,
            bd=0,
            pady=10,
            cursor="hand2",
            relief="flat",
            command=self.imprimir_codigo,
            state="disabled",
            activebackground="#d97706",
            activeforeground=T.WHITE,
        )
        self.btn_imprimir.pack(side="left", padx=6, ipadx=12)

        self.btn_limpiar = tk.Button(
            buttons_frame,
            text="Limpiar",
            font=F_BODY_B,
            bg=T.POS_BTN_ALT,
            fg=T.WHITE,
            bd=0,
            pady=10,
            cursor="hand2",
            relief="flat",
            command=self.limpiar_todo,
            activebackground=T.TEXT_MUTED,
            activeforeground=T.WHITE,
        )
        self.btn_limpiar.pack(side="left", padx=6, ipadx=12)

        self.btn_cerrar = tk.Button(
            buttons_frame,
            text="Cerrar",
            font=F_BODY_B,
            bg=T.DANGER,
            fg=T.WHITE,
            bd=0,
            pady=10,
            cursor="hand2",
            relief="flat",
            command=self.cerrar_ventana,
            activebackground="#b91c1c",
            activeforeground=T.WHITE,
        )
        self.btn_cerrar.pack(side="right", ipadx=16)
    
    def create_footer(self):
        """Crea el pie de página"""
        footer_frame = tk.Frame(self.cuerpo, bg=T.FOOTER, height=40)
        footer_frame.pack(fill="x")
        footer_frame.pack_propagate(False)

        tk.Label(
            footer_frame,
            text="VmPOS · Generador de códigos de barras",
            font=F_SMALL,
            bg=T.FOOTER,
            fg=T.HEADER_TEXT_DIM,
        ).pack(pady=12)
    
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
        """Genera código real estándar usando python-barcode + Pillow."""
        if not PIL_DISPONIBLE:
            messagebox.showerror("❌ Error", "PIL/Pillow no está disponible.\nInstale con: pip install Pillow")
            return None
        if not BARCODE_LIB_DISPONIBLE:
            messagebox.showerror("❌ Error", "python-barcode no está disponible.\nInstale con: pip install python-barcode")
            return None

        fmt = (formato or "CODE128").upper().strip()
        mapa = {
            "CODE128": "code128",
            "CODE39": "code39",
            "EAN13": "ean13",
            "EAN8": "ean8",
            "UPC-A": "upc",
            "ITF": "itf",
        }
        nombre_bc = mapa.get(fmt, "code128")
        writer_options = {
            "module_width": 0.28,   # barras suficientemente anchas para lectores comunes
            "module_height": 22.0,
            "quiet_zone": 6.5,
            "font_size": 12,
            "text_distance": 3,
            "write_text": bool(self.mostrar_texto.get()),
            "dpi": 300,
            "background": "white",
            "foreground": "black",
        }
        cls = barcode.get_barcode_class(nombre_bc)
        kwargs = {}
        if nombre_bc == "code39":
            kwargs["add_checksum"] = bool(self.incluir_checksum.get())
        bc = cls(texto, writer=ImageWriter(), **kwargs)
        return bc.render(writer_options=writer_options)
    
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
        """Cierra el generador y vuelve a mostrar el menú si estaba oculto."""
        master = self.ventana.master
        self.ventana.destroy()
        if master is not None:
            try:
                master.wm_deiconify()
                master.lift()
                master.focus_force()
            except tk.TclError:
                pass

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