import sys
import os
import sqlite3
import pandas as pd
import subprocess
from tkinter import Toplevel, StringVar, messagebox, simpledialog
from tkinter import Tk
from tkinter.ttk import Label, Entry, Button, Treeview, Scrollbar, Style

# ✅ Verifica y actualiza la estructura de la base de datos
def verificar_estructura_db():
    ruta_db = os.path.join(os.path.dirname(__file__), "..", "database", "ventas.db")
    conn = sqlite3.connect(ruta_db)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE productos ADD COLUMN costo REAL")
        print("✅ Columna 'costo' agregada correctamente.")
    except Exception as e:
        print("⚠️ Estructura intacta o ya existente:", e)
    conn.commit()
    conn.close()

# Verifica estructura antes de continuar
verificar_estructura_db()

# 🛒 Funciones de venta
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from modules.productos import buscar_producto_por_codigo
from modules.ventas import registrar_venta
from modules.impresora import generar_factura
from modules.caja import abrir_caja

def iniciar_venta():
    codigo = codigo_entry.get()
    producto = buscar_producto_por_codigo(codigo)

    if producto:
        total = float(producto['precio'])
        pagado = simpledialog.askfloat("💰 Pago recibido", f"🛍️ Total: ${total:.2f}\n\nIngrese el monto pagado:")

        if pagado is None:
            return
        if pagado < total:
            messagebox.showerror("⛔ Pago insuficiente", "El monto recibido es menor al total.")
            return

        cambio = pagado - total
        registrar_venta(producto)
        abrir_caja()
        generar_factura(producto)

        messagebox.showinfo("✅ Venta realizada", f"Producto: '{producto['nombre']}'\nTotal: ${total:.2f}\nPagado: ${pagado:.2f}\nCambio: ${cambio:.2f}")
        codigo_entry.delete(0, "end")
    else:
        messagebox.showerror("🔍 Error", "Producto no encontrado.")

def abrir_historial():
    ruta = os.path.join(os.path.dirname(__file__), "..", "ventas.csv")
    try:
        subprocess.Popen(["start", ruta], shell=True)
    except Exception as e:
        messagebox.showerror("❌ Error", f"No se pudo abrir el historial: {e}")

def mostrar_historial_en_ventana():
    ruta = os.path.join(os.path.dirname(__file__), "..", "ventas.csv")
    try:
        df = pd.read_csv(ruta)
        historial_ventana = Toplevel(ventana)
        historial_ventana.title("🧾 Historial de Ventas")
        historial_ventana.geometry("750x500")

        filtro_fecha = StringVar()
        filtro_producto = StringVar()

        Label(historial_ventana, text="🗓️ Filtrar por fecha (YYYY-MM-DD):").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        Entry(historial_ventana, textvariable=filtro_fecha).grid(row=0, column=1, padx=10, pady=5)

        Label(historial_ventana, text="🔤 Filtrar por producto:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        Entry(historial_ventana, textvariable=filtro_producto).grid(row=1, column=1, padx=10, pady=5)

        def aplicar_filtros():
            df_filtrado = df.copy()
            fecha = filtro_fecha.get()
            producto = filtro_producto.get()
            if fecha:
                df_filtrado = df_filtrado[df_filtrado['Fecha'].str.startswith(fecha)]
            if producto:
                df_filtrado = df_filtrado[df_filtrado['Producto'].str.contains(producto, case=False)]

            tree.delete(*tree.get_children())
            for _, row in df_filtrado.iterrows():
                tree.insert("", "end", values=list(row))

        Button(historial_ventana, text="🔎 Aplicar filtros", command=aplicar_filtros).grid(row=2, column=0, columnspan=2, pady=10)

        tree = Treeview(historial_ventana, columns=list(df.columns), show="headings")
        for col in df.columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        tree.grid(row=3, column=0, columnspan=2, padx=10, pady=5)

        scrollbar = Scrollbar(historial_ventana, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=3, column=2, sticky="ns")

        historial_ventana.grid_rowconfigure(3, weight=1)
        historial_ventana.grid_columnconfigure(1, weight=1)

        for _, row in df.iterrows():
            tree.insert("", "end", values=list(row))
    except Exception as e:
        messagebox.showerror("❌ Error", f"No se pudo mostrar el historial: {e}")

# 🪟 Interfaz principal
ventana = Tk()
ventana.title("🌸 Sistema de Ventas - Variedades Marce")
ventana.geometry("450x280")
ventana.configure(bg="#FFE4F1")  # Rosado suave

style = Style()
style.configure("TButton", font=("Segoe UI", 10), padding=5, background="#FFC0CB")  # Botones rosas
style.configure("TLabel", font=("Segoe UI", 10), background="#FFE4F1")

Label(ventana, text="📦 Código de producto:", background="#FFE4F1").grid(row=0, column=0, padx=10, pady=10, sticky="e")
codigo_entry = Entry(ventana, font=("Segoe UI", 10))
codigo_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")

Button(ventana, text="💳 Realizar venta", command=iniciar_venta).grid(row=1, column=0, columnspan=2, pady=5)
Button(ventana, text="📊 Historial de ventas (Excel)", command=abrir_historial).grid(row=2, column=0, columnspan=2, pady=5)
Button(ventana, text="🖥️ Ver historial en pantalla", command=mostrar_historial_en_ventana).grid(row=3, column=0, columnspan=2, pady=5)

ventana.grid_columnconfigure(1, weight=1)
ventana.mainloop()
