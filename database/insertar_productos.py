import sqlite3
import os

# Ruta dinámica para portabilidad
ruta_db = os.path.join(os.path.dirname(__file__), "database", "ventas.db")
conn = sqlite3.connect(ruta_db)
cursor = conn.cursor()

productos = [
    ("Manzana", 1200, 600, 50, "001"),
    ("Pan", 1500, 900, 100, "002"),
    ("Leche", 4300, 2600, 30, "003"),
    ("Café", 5200, 3100, 20, "004"),
    ("Jugo", 3600, 2200, 25, "005"),
]

for nombre, precio, costo, stock, codigo in productos:
    cursor.execute("""
        INSERT INTO productos (nombre, precio, costo, stock, codigo)
        VALUES (?, ?, ?, ?, ?)""", (nombre, precio, costo, stock, codigo))

conn.commit()
conn.close()
print("✅ Productos insertados correctamente con stock y costo.")
