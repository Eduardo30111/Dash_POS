import sqlite3

def buscar_producto_por_codigo(codigo):
    conn = sqlite3.connect("database/ventas.db")
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, precio FROM productos WHERE codigo = ?", (codigo,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado
