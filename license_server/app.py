# -*- coding: utf-8 -*-
"""
Panel y API mínimos para activar/desactivar instalaciones VmPOS por ``license_key``.
Soporta período por tienda (fecha inicio / fin) y caducidad automática al vencer.

Uso rápido:
  set VMPOS_LICENSE_ADMIN_TOKEN=Eduardo2180
  pip install -r requirements.txt
  python app.py

Abra http://127.0.0.1:5050 (o el host que configure). En la app cliente copie
database/license_remote.example.json a database/license_remote.json y ponga
la misma URL y la misma clave que registre aquí.
"""
from __future__ import annotations

import os
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template_string, request, url_for
try:
    import psycopg
    from psycopg.rows import dict_row
except Exception:  # pragma: no cover - fallback local sin postgres
    psycopg = None
    dict_row = None

APP = Flask(__name__)

DATA_DIR = Path(__file__).resolve().parent / "data"
DB_PATH = DATA_DIR / "licenses.sqlite"
DATABASE_URL = (os.environ.get("DATABASE_URL") or "").strip()


def _is_postgres_enabled() -> bool:
    return bool(DATABASE_URL)


def _normalized_database_url() -> str:
    url = DATABASE_URL
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    return url


def _sql(q: str) -> str:
    """Convierte placeholders ? a %s cuando se usa PostgreSQL."""
    if _is_postgres_enabled():
        return q.replace("?", "%s")
    return q


def _admin_token() -> str:
    # Por defecto coincide con run.cmd; en producción use VMPOS_LICENSE_ADMIN_TOKEN.
    return (os.environ.get("VMPOS_LICENSE_ADMIN_TOKEN") or "Eduardo2180").strip()


def _db() -> sqlite3.Connection:
    if _is_postgres_enabled():
        if psycopg is None:
            raise RuntimeError("PostgreSQL configurado pero psycopg no está instalado.")
        return psycopg.connect(_normalized_database_url(), row_factory=dict_row)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today_utc() -> str:
    """Fecha calendario UTC YYYY-MM-DD (comparación con period_* guardados así)."""
    return datetime.now(timezone.utc).date().isoformat()


def _parse_iso_date(s: str | None) -> datetime | None:
    if not s or not str(s).strip():
        return None
    raw = str(s).strip()[:10]
    try:
        return datetime.strptime(raw, "%Y-%m-%d")
    except ValueError:
        return None


def _ensure_license_columns(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    if _is_postgres_enabled():
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema='public' AND table_name='licenses'
            """
        )
        have = {r["column_name"] for r in cur.fetchall()}
        for col in ("period_start", "period_end"):
            if col not in have:
                cur.execute(f"ALTER TABLE licenses ADD COLUMN IF NOT EXISTS {col} TEXT")
    else:
        cur.execute("PRAGMA table_info(licenses)")
        have = {r[1] for r in cur.fetchall()}
        for col in ("period_start", "period_end"):
            if col not in have:
                try:
                    cur.execute(f"ALTER TABLE licenses ADD COLUMN {col} TEXT")
                except sqlite3.OperationalError:
                    pass
    conn.commit()


def _deactivate_expired(conn: sqlite3.Connection) -> None:
    """Marca is_active=0 si ya pasó period_end (solo filas con fin definido)."""
    today = _today_utc()
    conn.execute(
        _sql("""
        UPDATE licenses SET is_active = 0, updated_at = ?
        WHERE period_end IS NOT NULL AND TRIM(period_end) != ''
          AND period_end < ?
          AND is_active = 1
        """),
        (_utc_now(), today),
    )


def _effective_license_active(row: sqlite3.Row | None) -> tuple[bool, str]:
    """
    Activa solo si is_active y hoy está en [period_start, period_end] cuando existan.
    period_* son TEXT 'YYYY-MM-DD' (UTC calendario).
    """
    if row is None:
        return False, "Clave no registrada"
    if not bool(row["is_active"]):
        return False, "Licencia desactivada por el administrador"
    ps_raw = row["period_start"] if "period_start" in row.keys() else None
    pe_raw = row["period_end"] if "period_end" in row.keys() else None
    today_s = _today_utc()
    d_ps = _parse_iso_date(ps_raw)
    d_pe = _parse_iso_date(pe_raw)
    if d_ps and today_s < d_ps.strftime("%Y-%m-%d"):
        return False, "El período de la licencia aún no ha comenzado."
    if d_pe and today_s > d_pe.strftime("%Y-%m-%d"):
        return False, "El período de la licencia ha vencido."
    return True, "OK"


def _days_remaining_display(period_end: str | None) -> str:
    if not period_end or not str(period_end).strip():
        return "—"
    d_pe = _parse_iso_date(period_end)
    if not d_pe:
        return "—"
    n = (d_pe.date() - datetime.now(timezone.utc).date()).days
    if n < 0:
        return f"vencida ({-n} d.)"
    if n == 0:
        return "hoy"
    return f"{n} d."


def init_db():
    conn = _db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS licenses (
            license_key TEXT PRIMARY KEY,
            label TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            updated_at TEXT,
            last_client_check TEXT
        )
        """
    )
    conn.commit()
    _ensure_license_columns(conn)
    # Clave de demostración (cambie o elimine en producción)
    conn.execute(
        _sql("""
        INSERT INTO licenses (license_key, label, is_active, updated_at)
        VALUES ('VmPOS-DEMO-001', 'Demostración', 1, ?)
        ON CONFLICT(license_key) DO NOTHING
        """),
        (_utc_now(),),
    )
    conn.commit()
    _deactivate_expired(conn)
    conn.commit()
    conn.close()


PAGE = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>VmPOS · Licencias</title>
  <style>
    :root{
      --bg:#0b1220;
      --surface:#111a2e;
      --surface-2:#17253f;
      --line:#243552;
      --text:#e6edf8;
      --muted:#95a7c4;
      --ok:#16a34a;
      --off:#ef4444;
      --warn:#f59e0b;
      --brand:#3b82f6;
    }
    * { box-sizing: border-box; }
    body {
      font-family: "Inter", "Segoe UI", system-ui, sans-serif;
      background: radial-gradient(circle at top, #13233f 0%, var(--bg) 48%);
      color: var(--text);
      margin: 0;
      min-height: 100vh;
      padding: 20px 14px 28px;
    }
    .container { max-width: 1200px; margin: 0 auto; }
    .header {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 14px;
    }
    h1 { margin: 0; font-size: clamp(1.1rem, 3.8vw, 1.65rem); letter-spacing: .2px; }
    .sub { color: var(--muted); margin: 4px 0 0; font-size: .92rem; }
    .api-chip {
      border: 1px solid var(--line);
      background: rgba(23, 37, 63, .8);
      color: var(--muted);
      padding: 8px 12px;
      border-radius: 999px;
      font-size: .8rem;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 100%;
      white-space: nowrap;
    }
    .stats {
      display: grid;
      grid-template-columns: repeat(4, minmax(130px, 1fr));
      gap: 10px;
      margin: 14px 0 16px;
    }
    .stat {
      background: linear-gradient(180deg, #17253f 0%, #121e34 100%);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 10px 12px;
      min-height: 74px;
    }
    .stat .k { color: var(--muted); font-size: .76rem; text-transform: uppercase; letter-spacing: .08em; }
    .stat .v { margin-top: 6px; font-size: 1.35rem; font-weight: 750; }
    .grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 12px;
    }
    .card {
      background: linear-gradient(180deg, rgba(23, 37, 63, .92), rgba(17, 26, 46, .96));
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 16px;
      box-shadow: 0 12px 30px rgba(0, 0, 0, .24);
    }
    h2.card-title { margin: 0 0 8px; font-size: 1rem; }
    .help { color: var(--muted); font-size: .86rem; margin: 0 0 8px; }
    .form-grid {
      display: grid;
      grid-template-columns: repeat(5, minmax(140px, 1fr));
      gap: 10px;
      align-items: end;
    }
    .field label {
      display:block;
      margin-bottom: 5px;
      color: var(--muted);
      font-size:.74rem;
      letter-spacing:.02em;
    }
    input[type=text], input[type=date] {
      width: 100%;
      border: 1px solid #33496c;
      background: #0f182b;
      color: var(--text);
      border-radius: 8px;
      padding: 9px 10px;
      outline: none;
    }
    input[type=text]:focus, input[type=date]:focus { border-color: #60a5fa; box-shadow: 0 0 0 2px rgba(96,165,250,.2); }
    input[type=date] { color-scheme: dark; }
    button {
      cursor: pointer;
      border: none;
      border-radius: 8px;
      padding: 9px 13px;
      font-weight: 700;
      font-size: .84rem;
      white-space: nowrap;
    }
    .danger { background: var(--off); color: #fff; }
    .safe { background: var(--ok); color: #052e16; }
    .muted-btn { background: #3c4f71; color: #fff; }
    .primary { background: var(--brand); color: #fff; }
    .ghost { background: transparent; color: #fca5a5; border: 1px solid #7f1d1d; }
    .pill {
      display:inline-flex;
      align-items:center;
      border-radius: 999px;
      padding: 3px 10px;
      font-size: .75rem;
      font-weight: 700;
    }
    .on { background: #064e3b; color: #6ee7b7; }
    .off { background: #4a1313; color: #fda4af; }
    .warn { background: #4a3009; color: #fcd34d; }
    .table-wrap { overflow: auto; border: 1px solid var(--line); border-radius: 10px; }
    table { width: 100%; border-collapse: collapse; min-width: 880px; font-size: .86rem; }
    th, td { text-align: left; padding: 11px 10px; border-bottom: 1px solid var(--line); vertical-align: middle; }
    th { color: var(--muted); font-size: .76rem; text-transform: uppercase; letter-spacing: .05em; position: sticky; top: 0; background: #111b30; }
    td small { color: var(--muted); }
    tr:hover td { background: rgba(148,163,184,.06); }
    form.inline { display: inline-flex; margin: 0; }
    .footer-note { color: var(--muted); font-size: .84rem; margin-top: 12px; }
    code { background: #0c1528; border: 1px solid #243552; padding: 2px 6px; border-radius: 6px; }

    @media (max-width: 980px){
      .stats { grid-template-columns: repeat(2, minmax(120px, 1fr)); }
      .form-grid { grid-template-columns: repeat(2, minmax(130px, 1fr)); }
      .form-grid .action { grid-column: span 2; }
    }
    @media (max-width: 620px){
      body { padding: 12px 10px 20px; }
      .header { align-items: flex-start; }
      .stats { grid-template-columns: 1fr 1fr; gap: 8px; }
      .card { padding: 12px; border-radius: 12px; }
      .form-grid { grid-template-columns: 1fr; }
      .form-grid .action { grid-column: span 1; }
      .table-wrap { border: none; overflow: visible; }
      table, thead, tbody, th, td, tr { display: block; min-width: 0; }
      thead { display: none; }
      tr {
        border: 1px solid var(--line);
        border-radius: 10px;
        margin-bottom: 9px;
        overflow: hidden;
        background: rgba(12, 21, 40, .55);
      }
      td {
        border-bottom: 1px solid rgba(51,73,108,.5);
        padding: 8px 10px;
        display: flex;
        justify-content: space-between;
        gap: 8px;
      }
      td::before {
        content: attr(data-label);
        color: var(--muted);
        font-weight: 600;
        font-size: .75rem;
      }
      td:last-child { border-bottom: none; }
      td[data-label="Acciones"] { justify-content: flex-end; }
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div>
        <h1>Panel de control de licencias VmPOS</h1>
        <p class="sub">Administre tiendas, periodos y activaciones desde una vista clara para PC y celular.</p>
      </div>
      <div class="api-chip">API: <code>GET /api/license/&lt;clave&gt;/status</code></div>
    </div>

    <div class="stats">
      <div class="stat"><div class="k">Total licencias</div><div class="v">{{ total_licenses }}</div></div>
      <div class="stat"><div class="k">Activas</div><div class="v">{{ active_licenses }}</div></div>
      <div class="stat"><div class="k">Desactivadas</div><div class="v">{{ inactive_licenses }}</div></div>
      <div class="stat"><div class="k">Vencen en 7 días</div><div class="v">{{ expiring_soon }}</div></div>
    </div>

    <div class="grid">
      <div class="card">
        <h2 class="card-title">Crear tienda (con periodo)</h2>
        <p class="help">Si deja la clave vacia se genera automaticamente. El cliente usara esa clave en <code>license_remote.json</code>.</p>
        <form method="post" action="{{ url_for('add_tienda') }}" class="form-grid">
          <input type="hidden" name="admin_token" value="{{ token }}"/>
          <div class="field">
            <label>Clave (opcional)</label>
            <input type="text" name="license_key" placeholder="Vacio = generar VM-..." maxlength="120"/>
          </div>
          <div class="field">
            <label>Nombre tienda / etiqueta</label>
            <input type="text" name="label" placeholder="Ej: Papeleria Centro" required maxlength="200"/>
          </div>
          <div class="field">
            <label>Fecha inicio</label>
            <input type="date" name="period_start" required/>
          </div>
          <div class="field">
            <label>Fecha fin</label>
            <input type="date" name="period_end" required/>
          </div>
          <div class="field action">
            <button type="submit" class="primary">Crear tienda</button>
          </div>
        </form>
      </div>

      <div class="card">
        <h2 class="card-title">Registrar licencia manual</h2>
        <p class="help">Use esta opcion cuando no necesite periodo obligatorio.</p>
        <form method="post" action="{{ url_for('add_license') }}" class="form-grid">
          <input type="hidden" name="admin_token" value="{{ token }}"/>
          <div class="field">
            <label>Clave</label>
            <input type="text" name="license_key" placeholder="EJ: TIENDA-CALI-01" required maxlength="120"/>
          </div>
          <div class="field">
            <label>Etiqueta</label>
            <input type="text" name="label" placeholder="Nombre del cliente" maxlength="200"/>
          </div>
          <div class="field">
            <label>Inicio (opcional)</label>
            <input type="date" name="period_start"/>
          </div>
          <div class="field">
            <label>Fin (opcional)</label>
            <input type="date" name="period_end"/>
          </div>
          <div class="field action">
            <button type="submit" class="muted-btn">Registrar licencia</button>
          </div>
        </form>
      </div>

      <div class="card">
        <h2 class="card-title">Licencias registradas</h2>
        <div class="table-wrap">
          <table>
            <thead><tr>
              <th>Clave</th><th>Tienda</th><th>Inicio</th><th>Fin</th><th>Restante</th>
              <th>Estado</th><th>Ultimo check</th><th>Acciones</th>
            </tr></thead>
            <tbody>
            {% for r in rows %}
              <tr>
                <td data-label="Clave"><code>{{ r.license_key }}</code></td>
                <td data-label="Tienda">{{ r.label or "—" }}</td>
                <td data-label="Inicio"><small>{{ r.period_start or "—" }}</small></td>
                <td data-label="Fin"><small>{{ r.period_end or "—" }}</small></td>
                <td data-label="Restante" style="color:{% if r.dias_restantes is not none and r.dias_restantes < 0 %}var(--off){% elif r.dias_restantes is not none and r.dias_restantes <= 7 %}var(--warn){% else %}var(--muted){% endif %};">
                  {% if r.period_end %}
                    {% if r.dias_restantes is not none %}
                      {% if r.dias_restantes < 0 %}Vencida{% elif r.dias_restantes == 0 %}Ultimo dia{% else %}{{ r.dias_restantes }} dia{% if r.dias_restantes != 1 %}s{% endif %}{% endif %}
                    {% else %}—{% endif %}
                  {% else %}—{% endif %}
                </td>
                <td data-label="Estado">{% if r.is_active %}<span class="pill on">ACTIVA</span>{% else %}<span class="pill off">DESACTIVADA</span>{% endif %}</td>
                <td data-label="Ultimo check"><small>{{ r.last_client_check or "—" }}</small></td>
                <td data-label="Acciones" style="display:flex; gap:8px; flex-wrap:wrap;">
                  {% if r.is_active %}
                  <form class="inline" method="post" action="{{ url_for('toggle_license', key=r.license_key) }}"
                        onsubmit="return confirm('¿Desactivar esta instalación?');">
                    <input type="hidden" name="admin_token" value="{{ token }}"/>
                    <input type="hidden" name="active" value="0"/>
                    <button type="submit" class="danger">Desactivar</button>
                  </form>
                  {% else %}
                  <form class="inline" method="post" action="{{ url_for('toggle_license', key=r.license_key) }}">
                    <input type="hidden" name="admin_token" value="{{ token }}"/>
                    <input type="hidden" name="active" value="1"/>
                    <button type="submit" class="safe">Activar</button>
                  </form>
                  {% endif %}
                  <form class="inline" method="post" action="{{ url_for('delete_license', key=r.license_key) }}"
                        onsubmit="return confirm('¿Eliminar esta tienda/licencia de forma permanente?');">
                    <input type="hidden" name="admin_token" value="{{ token }}"/>
                    <button type="submit" class="ghost">Eliminar</button>
                  </form>
                </td>
              </tr>
            {% else %}
              <tr><td colspan="8" style="color:var(--muted);">No hay licencias registradas.</td></tr>
            {% endfor %}
            </tbody>
          </table>
        </div>
        <p class="footer-note">Tip: para mayor seguridad configure <code>VMPOS_LICENSE_ADMIN_TOKEN</code> con un valor largo y privado.</p>
      </div>
    </div>
  </div>
</body>
</html>
"""

LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"/><title>Acceso panel VmPOS</title>
<style>body{background:#0f172a;color:#e2e8f0;font-family:Segoe UI,sans-serif;padding:40px;max-width:420px;margin:auto;}
input{width:100%;padding:10px;margin:8px 0;border-radius:6px;border:1px solid #475569;background:#1e293b;color:#fff;}
button{margin-top:12px;padding:10px 18px;border-radius:6px;border:none;background:#3b82f6;color:white;font-weight:600;cursor:pointer;}
p{color:#94a3b8;font-size:0.9rem;}</style></head>
<body>
  <h2>Panel de licencias</h2>
  <p>Introduzca el mismo token que definió en <code>VMPOS_LICENSE_ADMIN_TOKEN</code>.</p>
  <form method="post" action="{{ url_for('login') }}">
    <input type="password" name="admin_token" placeholder="Token de administrador" required autocomplete="off"/>
    <button type="submit">Entrar</button>
  </form>
</body></html>
"""


def _enrich_row_for_dashboard(row: sqlite3.Row) -> dict:
    d = dict(row)
    pe = d.get("period_end")
    d["dias_restantes"] = None
    if pe and str(pe).strip():
        dt = _parse_iso_date(str(pe))
        if dt:
            d["dias_restantes"] = (dt.date() - datetime.now(timezone.utc).date()).days
    return d


@APP.route("/")
def index():
    tok = request.args.get("token", "").strip()
    if tok and tok == _admin_token():
        return redirect(url_for("dashboard", token=tok))
    return render_template_string(LOGIN_PAGE)


@APP.route("/login", methods=["POST"])
def login():
    tok = request.form.get("admin_token", "").strip()
    if tok != _admin_token():
        return render_template_string(LOGIN_PAGE + "<p style='color:#f87171'>Token incorrecto.</p>")
    return redirect(url_for("dashboard", token=tok))


@APP.route("/dashboard")
def dashboard():
    tok = request.args.get("token", "").strip()
    if tok != _admin_token():
        return redirect(url_for("index"))
    conn = _db()
    _ensure_license_columns(conn)
    _deactivate_expired(conn)
    conn.commit()
    raw = conn.execute(
        """
        SELECT license_key, label, is_active, last_client_check, period_start, period_end
        FROM licenses ORDER BY license_key
        """
    ).fetchall()
    rows = [_enrich_row_for_dashboard(r) for r in raw]
    total_licenses = len(rows)
    active_licenses = sum(1 for r in rows if bool(r.get("is_active")))
    inactive_licenses = total_licenses - active_licenses
    expiring_soon = sum(
        1
        for r in rows
        if r.get("dias_restantes") is not None and 0 <= int(r.get("dias_restantes")) <= 7
    )
    conn.close()
    return render_template_string(
        PAGE,
        rows=rows,
        token=tok,
        total_licenses=total_licenses,
        active_licenses=active_licenses,
        inactive_licenses=inactive_licenses,
        expiring_soon=expiring_soon,
    )


def _normalize_period_dates(ps: str | None, pe: str | None) -> tuple[str | None, str | None]:
    a = (ps or "").strip()[:10] or None
    b = (pe or "").strip()[:10] or None
    return a, b


@APP.route("/license/add", methods=["POST"])
def add_license():
    tok_in = request.form.get("admin_token", "").strip()
    if tok_in != _admin_token():
        return jsonify({"error": "unauthorized"}), 401
    key = (request.form.get("license_key") or "").strip()
    label = (request.form.get("label") or "").strip()
    ps, pe = _normalize_period_dates(
        request.form.get("period_start"),
        request.form.get("period_end"),
    )
    if not key:
        return redirect(url_for("dashboard", token=tok_in))
    conn = _db()
    _ensure_license_columns(conn)
    conn.execute(
        _sql("""
        INSERT INTO licenses (license_key, label, is_active, updated_at, period_start, period_end)
        VALUES (?, ?, 1, ?, ?, ?)
        ON CONFLICT(license_key) DO UPDATE SET
            label=excluded.label,
            updated_at=excluded.updated_at,
            period_start=COALESCE(excluded.period_start, licenses.period_start),
            period_end=COALESCE(excluded.period_end, licenses.period_end)
        """),
        (key, label or None, _utc_now(), ps, pe),
    )
    conn.commit()
    _deactivate_expired(conn)
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard", token=tok_in))


@APP.route("/license/tienda", methods=["POST"])
def add_tienda():
    tok_in = request.form.get("admin_token", "").strip()
    if tok_in != _admin_token():
        return jsonify({"error": "unauthorized"}), 401
    label = (request.form.get("label") or "").strip()
    key = (request.form.get("license_key") or "").strip()
    ps = (request.form.get("period_start") or "").strip()[:10]
    pe = (request.form.get("period_end") or "").strip()[:10]
    if not label or not ps or not pe:
        return redirect(url_for("dashboard", token=tok_in))
    d_ps = _parse_iso_date(ps)
    d_pe = _parse_iso_date(pe)
    if not d_ps or not d_pe:
        return redirect(url_for("dashboard", token=tok_in))
    if d_pe.date() < d_ps.date():
        return redirect(url_for("dashboard", token=tok_in))
    if not key:
        key = f"VM-{secrets.token_hex(4).upper()}"
    conn = _db()
    _ensure_license_columns(conn)
    conn.execute(
        _sql("""
        INSERT INTO licenses (license_key, label, is_active, updated_at, period_start, period_end)
        VALUES (?, ?, 1, ?, ?, ?)
        ON CONFLICT(license_key) DO UPDATE SET
            label=excluded.label,
            is_active=1,
            updated_at=excluded.updated_at,
            period_start=excluded.period_start,
            period_end=excluded.period_end
        """),
        (key, label, _utc_now(), ps, pe),
    )
    conn.commit()
    _deactivate_expired(conn)
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard", token=tok_in))


@APP.route("/license/<path:key>/toggle", methods=["POST"])
def toggle_license(key):
    tok = request.form.get("admin_token", "").strip()
    if tok != _admin_token():
        return jsonify({"error": "unauthorized"}), 401
    active = request.form.get("active") == "1"
    conn = _db()
    _ensure_license_columns(conn)
    conn.execute(
        _sql("UPDATE licenses SET is_active = ?, updated_at = ? WHERE license_key = ?"),
        (1 if active else 0, _utc_now(), key),
    )
    conn.commit()
    _deactivate_expired(conn)
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard", token=tok))


@APP.route("/license/<path:key>/delete", methods=["POST"])
def delete_license(key):
    tok = request.form.get("admin_token", "").strip()
    if tok != _admin_token():
        return jsonify({"error": "unauthorized"}), 401
    conn = _db()
    _ensure_license_columns(conn)
    conn.execute(_sql("DELETE FROM licenses WHERE license_key = ?"), (key.strip(),))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard", token=tok))


@APP.get("/api/license/<path:license_key>/status")
def api_status(license_key: str):
    conn = _db()
    _ensure_license_columns(conn)
    _deactivate_expired(conn)
    conn.commit()
    row = conn.execute(
        _sql("""
        SELECT license_key, label, is_active, period_start, period_end
        FROM licenses WHERE license_key = ?
        """),
        (license_key.strip(),),
    ).fetchone()
    if row:
        conn.execute(
            _sql("UPDATE licenses SET last_client_check = ? WHERE license_key = ?"),
            (_utc_now(), license_key.strip()),
        )
    conn.commit()
    conn.close()
    if not row:
        return jsonify({"active": False, "message": "Clave no registrada"}), 404
    ok, msg = _effective_license_active(row)
    if row and ok:
        return jsonify({"active": True, "message": msg})
    return jsonify({"active": False, "message": msg})


def main():
    init_db()
    token = _admin_token()
    if len(token) < 12:
        print("[VmPOS license_server] ADVERTENCIA: en producción use un token más largo (VMPOS_LICENSE_ADMIN_TOKEN).")
    host = os.environ.get("VMPOS_LICENSE_BIND", "0.0.0.0")
    port = int(os.environ.get("PORT") or os.environ.get("VMPOS_LICENSE_PORT", "5050"))
    print(f"[VmPOS license_server] http://127.0.0.1:{port}/  (bind {host}:{port})")
    APP.run(host=host, port=port, debug=os.environ.get("FLASK_DEBUG") == "1")


if __name__ == "__main__":
    main()
