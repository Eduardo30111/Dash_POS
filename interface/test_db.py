from usuarios_db import insertar_usuario, obtener_usuarios

def agregar_usuario_prueba():
    # Intenta insertar un usuario por defecto si no existe
    if insertar_usuario("admin", "admin123", "Administrador", "Activo"):
        print("Usuario 'admin' agregado exitosamente.")
    else:
        print("El usuario 'admin' ya existe o hubo un error al agregarlo.")

    if insertar_usuario("vendedor", "pass123", "Vendedor", "Activo"):
        print("Usuario 'vendedor' agregado exitosamente.")
    else:
        print("El usuario 'vendedor' ya existe o hubo un error al agregarlo.")

    print("\nUsuarios actuales en la base de datos:")
    for user in obtener_usuarios():
        # sqlite3.Row se comporta como un diccionario, así que puedes acceder con user['nombre_columna']
        print(f"ID: {user['id']}, Usuario: {user['usuario']}, Rol: {user['rol']}, Estado: {user['estado']}")

if __name__ == "__main__":
    agregar_usuario_prueba()