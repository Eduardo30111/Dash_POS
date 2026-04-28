# VmPOS license dashboard en Render + PostgreSQL

## 1) Subir proyecto a GitHub
- Sube este repositorio con los cambios actuales.

## 2) Crear PostgreSQL en Render
- En Render: `New` -> `PostgreSQL`.
- Nombre sugerido: `vmpos-license-db`.
- Espera a que quede `Available`.

## 3) Crear servicio Web en Render
- En Render: `New` -> `Web Service`.
- Conecta tu repo de GitHub.
- Configuracion:
  - `Root Directory`: `license_server`
  - `Build Command`: `pip install -r requirements.txt`
  - `Start Command`: `gunicorn app:APP --bind 0.0.0.0:$PORT`

## 4) Variables de entorno (obligatorio)
- `VMPOS_LICENSE_ADMIN_TOKEN` = tu token privado largo.
- `DATABASE_URL` = usa la cadena del PostgreSQL de Render.
  - Si creas el servicio y la DB en el mismo Blueprint (`render.yaml`), Render la conecta solo.

## 5) Migrar datos desde SQLite local a PostgreSQL
Desde tu PC (en carpeta `license_server`):

```bash
pip install -r requirements.txt
set DATABASE_URL=postgresql://USUARIO:PASS@HOST:PUERTO/DB
python migrate_sqlite_to_postgres.py
```

Opcional si tu SQLite origen esta en otra ruta:

```bash
set SQLITE_PATH=C:\ruta\licenses.sqlite
python migrate_sqlite_to_postgres.py
```

## 6) Verificar
- Abre la URL publica de Render.
- Inicia sesion con `VMPOS_LICENSE_ADMIN_TOKEN`.
- Revisa que aparezcan las tiendas/licencias.

## 7) Configurar clientes VmPOS
En cada tienda, en `license_remote.json`:
- `server_url`: URL publica de Render (ejemplo `https://vmpos-license-dashboard.onrender.com`)
- `license_key`: clave de esa tienda.

## Notas
- La app ahora usa PostgreSQL automaticamente si existe `DATABASE_URL`.
- Si no hay `DATABASE_URL`, sigue funcionando local con SQLite.
