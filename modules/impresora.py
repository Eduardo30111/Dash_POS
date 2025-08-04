from reportlab.lib.pagesizes import A7
from reportlab.pdfgen import canvas
from datetime import datetime
import os
import subprocess

def generar_factura(productos, total):
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    nombre_archivo = f"reports/factura_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"

    c = canvas.Canvas(nombre_archivo, pagesize=A7)
    c.setFont("Helvetica", 8)

    c.drawString(10, 110, "TIENDA EDUARDO")
    c.drawString(10, 100, f"Fecha: {fecha}")
    c.drawString(10, 90, "-" * 20)

    y = 80
    for nombre, precio in productos:
        c.drawString(10, y, f"{nombre} - ${precio:.2f}")
        y -= 10

    c.drawString(10, y - 10, "-" * 20)
    c.drawString(10, y - 20, f"TOTAL: ${total:.2f}")
    c.drawString(10, y - 30, "¡Gracias por su compra!")
    c.save()

    imprimir_pdf(nombre_archivo)

def imprimir_pdf(ruta_pdf):
    ruta_pdftoprinter = "PDFtoPrinter.exe"
    if os.path.exists(ruta_pdftoprinter):
        subprocess.run([ruta_pdftoprinter, ruta_pdf])
    else:
        print("No se encontró PDFtoPrinter.exe")
