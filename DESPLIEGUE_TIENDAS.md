# Despliegue VmPOS por tienda (instalador)

Este flujo genera un instalador `.exe` para instalar VmPOS en cada tienda con todas sus funciones.

## 1) Requisitos en el equipo de build

- Windows
- Python 3.10+ (ideal 3.12)
- Inno Setup 6

## 2) Generar instalador

Desde la raiz del proyecto:

1. Crear entorno virtual (si no existe):
   - `python -m venv .venv`
2. Ejecutar:
   - `build_installer.bat`

Salida esperada:
- `dist_installer\VmPOS-Setup.exe`

## 3) Instalar en una tienda

1. Copiar `VmPOS-Setup.exe` al PC de la tienda.
2. Ejecutar instalador.
3. VmPOS se instala en:
   - `%LOCALAPPDATA%\VmPOS`

> Se usa `AppData\Local` para que la app pueda escribir base de datos, reportes y backups sin errores de permisos.
>
> En instalaciones nuevas, VmPOS crea automaticamente la base de datos local del cliente
> en el primer inicio. No se empaquetan las DB del desarrollador para evitar arrastrar
> usuarios, ventas o configuraciones del entorno local.

## 3.1) Credenciales iniciales por defecto

- Usuario: `admin`
- Contrasena: `admin123`

Estas credenciales se crean automaticamente en la primera ejecucion si no existe
ningun administrador en la base de datos local.

## 4) Activar licencia remota por tienda

Despues de instalar, en la tienda editar:

- `%LOCALAPPDATA%\VmPOS\database\license_remote.json`

Campos clave:

```json
{
  "remote_check_enabled": true,
  "server_url": "http://TU-SERVIDOR:5050",
  "license_key": "CLAVE_DE_LA_TIENDA",
  "offline_grace_hours": 72
}
```

- `license_key`: clave creada en el dashboard de licencias.
- `server_url`: URL real del servidor (IP publica, DNS o VPN).

## 5) Actualizacion de tienda (nueva version)

1. Cerrar VmPOS.
2. Ejecutar el nuevo `VmPOS-Setup.exe`.
3. Reinstala encima y conserva datos locales (database/reportes/backups).

## 5.1) Si quieres reiniciar una tienda a estado inicial

En la carpeta de instalacion ejecuta:

- `reset_datos_cliente.bat`

Esto elimina la BD local del equipo y deja el sistema listo para recrearse limpio
en el siguiente inicio (`admin / admin123`).

## 6) Recomendaciones operativas

- Hacer backup periodico de `%LOCALAPPDATA%\VmPOS\database`.
- Si una tienda no usa licencia remota, dejar `remote_check_enabled` en `false`.
- Mantener token admin del `license_server` en variable de entorno y no hardcodeado en produccion.
