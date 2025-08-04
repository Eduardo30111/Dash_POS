import sqlite3
import os

# Ruta donde se guardará la nueva base
base_dir = os.path.dirname(__file__)
ruta_db = os.path.join(base_dir, 'ventas.db')

# Conexión y creación de tabla
conn = sqlite3.connect(ruta_db)
cursor = conn.cursor()

# Crear la tabla de productos
cursor.execute("""
CREATE TABLE IF NOT EXISTS productos (
    codigo TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    stock INTEGER NOT NULL,
    precio REAL NOT NULL
)
""")

# (Opcional) Insertar productos de ejemplo
productos_demo = [
    ("001", "Jabon líquido", 15, 3500),
    ("002", "Cepillo de dientes", 25, 2800),
    ("003", "Pañuelos faciales", 10, 4500)
]

cursor.executemany("INSERT INTO productos VALUES (?, ?, ?, ?)", productos_demo)

conn.commit()
conn.close()

print("✅ Base de datos creada con productos demo.")
