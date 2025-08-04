import csv
from datetime import datetime
import os

def registrar_venta(producto):
    ruta_archivo = os.path.join(os.path.dirname(__file__), "..", "ventas.csv")
    encabezado = ["Producto", "Precio", "Fecha"]

    venta = {
        "Producto": producto["nombre"],
        "Precio": producto["precio"],
        "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # Verifica si el archivo existe y si necesita encabezado
    agregar_encabezado = not os.path.isfile(ruta_archivo)

    # 🧾 Escribir la venta en el archivo CSV
    with open(ruta_archivo, mode="a", newline="", encoding="utf-8") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=encabezado)
        if agregar_encabezado:
            writer.writeheader()
        writer.writerow(venta)

    print(f"✅ Venta guardada: {venta}")
