import sqlite3
import os

ruta_db = os.path.join(os.path.dirname(__file__), "ventas.db")  # Asumiendo que ya estás dentro de /database
conn = sqlite3.connect(ruta_db)
cursor = conn.cursor()

# 🔄 Elimina la tabla si ya existe
cursor.execute("DROP TABLE IF EXISTS productos")

# 🧱 Crea la tabla productos con estructura completa
cursor.execute("""
CREATE TABLE productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    precio REAL NOT NULL,
    costo REAL NOT NULL,
    stock INTEGER NOT NULL,
    codigo TEXT UNIQUE NOT NULL
)
""")

# Las otras tablas (no necesitan recrearse si ya están bien)
cursor.execute("""
CREATE TABLE IF NOT EXISTS ventas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    total REAL NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS detalle_venta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venta_id INTEGER NOT NULL,
    producto TEXT NOT NULL,
    precio REAL NOT NULL,
    cantidad INTEGER NOT NULL,
    subtotal REAL NOT NULL,
    FOREIGN KEY (venta_id) REFERENCES ventas(id)
)
""")

conn.commit()
conn.close()
print("✅ Base de datos inicializada correctamente.")
