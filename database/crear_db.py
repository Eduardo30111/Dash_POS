import sqlite3
import os

# Definir la ruta de la base de datos
base_dir = os.path.dirname(os.path.abspath(__file__))
database_dir = os.path.join(base_dir, '..', 'database')
ruta_db = os.path.join(database_dir, 'ventas.db')

# Crear el directorio 'database' si no existe
if not os.path.exists(database_dir):
    os.makedirs(database_dir)
    print(f"Directorio creado: {database_dir}")

conn = None
try:
    conn = sqlite3.connect(ruta_db)
    cursor = conn.cursor()

    # Opcional: Eliminar tablas existentes para empezar de cero
    # cursor.execute("DROP TABLE IF EXISTS productos")
    # cursor.execute("DROP TABLE IF EXISTS ventas")
    # cursor.execute("DROP TABLE IF EXISTS detalle_ventas")
    # print("Tablas existentes eliminadas.")

    # Crear la tabla de productos (si no existe)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            codigo TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            stock INTEGER NOT NULL,
            precio REAL NOT NULL
        )
    """)
    print("Tabla 'productos' verificada.")

    # Crear la tabla de ventas (si no existe)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ventas (
            id_venta INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_venta TEXT NOT NULL,
            hora_venta TEXT NOT NULL,
            documento_cliente TEXT NOT NULL,
            total_venta REAL NOT NULL
        )
    """)
    print("Tabla 'ventas' verificada.")

    # Crear la tabla de detalle_ventas (si no existe)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detalle_ventas (
            id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
            id_venta INTEGER NOT NULL,
            codigo_producto TEXT NOT NULL,
            nombre_producto TEXT NOT NULL,
            precio_unitario REAL NOT NULL,
            cantidad INTEGER NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY(id_venta) REFERENCES ventas(id_venta),
            FOREIGN KEY(codigo_producto) REFERENCES productos(codigo)
        )
    """)
    print("Tabla 'detalle_ventas' verificada.")
    
    # 🆕 Crear la nueva tabla de reportes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reportes (
            id_reporte INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            fecha_inicio TEXT NOT NULL,
            fecha_fin TEXT NOT NULL,
            resumen TEXT,
            ruta_pdf TEXT
        )
    """)
    print("Tabla 'reportes' creada exitosamente.")

    # Insertar datos de ejemplo solo si la tabla está vacía
    cursor.execute("SELECT COUNT(*) FROM productos")
    if cursor.fetchone()[0] == 0:
        productos_ejemplo = [
            ('101', 'Esponja de Maquillaje', 50, 15000),
            ('102', 'Lápiz Labial Rojo', 100, 25000),
            ('103', 'Kit de Sombras', 20, 45000),
            ('104', 'Brocha de Polvo', 75, 30000),
            ('105', 'Esmalte de Uñas', 200, 8000),
            ('106', 'Delineador Negro', 80, 18000),
            ('107', 'Mascara de Pestañas', 60, 22000),
            ('108', 'Crema Hidratante', 40, 50000),
            ('109', 'Perfume Floral', 30, 85000),
            ('110', 'Shampoo Seco', 90, 12000),
        ]
        cursor.executemany("INSERT INTO productos (codigo, nombre, stock, precio) VALUES (?, ?, ?, ?)", productos_ejemplo)
        conn.commit()
        print("Datos de ejemplo insertados en la tabla 'productos'.")
    else:
        print("La tabla 'productos' ya contiene datos.")
        
    print("La base de datos 'ventas.db' se ha verificado y configurado con éxito.")

except sqlite3.OperationalError as e:
    print(f"Error de base de datos: {e}")
    print("Asegúrate de que ningún otro programa esté usando el archivo ventas.db.")
except Exception as e:
    print(f"Ocurrió un error inesperado: {e}")
finally:
    if conn:
        conn.close()
        print("Conexión a la base de datos cerrada.")

