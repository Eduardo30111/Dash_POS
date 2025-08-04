# Script temporal para inicializar el permiso de "Ventas" para usuarios existentes
from usuarios_db import obtener_usuarios, inicializar_permisos_usuario, insertar_permiso

def inicializar_permiso_ventas_existentes():
    usuarios_existentes = obtener_usuarios()
    print("Inicializando permiso 'Ventas' para usuarios existentes...")
    for user in usuarios_existentes:
        # Intentar insertar el permiso "Ventas" con acceso 0 (por defecto)
        # Si ya existe por alguna razón, insert_permiso retornará False y no hará nada.
        if insertar_permiso(user['id'], "Ventas", 0):
            print(f"Permiso 'Ventas' inicializado para el usuario ID: {user['id']} ({user['usuario']})")
        else:
            print(f"Permiso 'Ventas' ya existe o hubo un problema para el usuario ID: {user['id']} ({user['usuario']})")
    print("Proceso completado.")

if __name__ == "__main__":
    inicializar_permiso_ventas_existentes()