# -*- coding: utf-8 -*-
"""
Control remoto de acceso: consulta un servidor propio para saber si la instalación
sigue autorizada.

Copie ``database/license_remote.example.json`` a ``database/license_remote.json``
y ajuste ``server_url`` y ``license_key`` para activarlo.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

from paths import license_remote_config_path

OFFLINE_GRACE_HOURS = 24.0
_STATE_FILE = ".license_state"
# Semilla local para firma anti-manipulación básica del estado offline.
# Nota: no sustituye seguridad de servidor, pero evita bypass trivial por editar JSON.
_LOCAL_SIGN_SEED = "VmPOS-LICENSE-LOCK-2026"


def _load_cfg() -> dict | None:
    p = license_remote_config_path()
    if not os.path.isfile(p):
        return None
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError, TypeError):
        return None


def _save_cfg(cfg: dict) -> None:
    p = license_remote_config_path()
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def _state_path() -> str:
    p = license_remote_config_path()
    return os.path.join(os.path.dirname(p), _STATE_FILE)


def _machine_fingerprint() -> str:
    host = os.environ.get("COMPUTERNAME", "")
    mac = str(uuid.getnode())
    raw = f"{host}|{mac}".encode("utf-8", errors="ignore")
    return hashlib.sha256(raw).hexdigest()


def _state_sig(license_key: str, last_ok_unix: int, fingerprint: str) -> str:
    msg = f"{license_key}|{int(last_ok_unix)}|{fingerprint}".encode("utf-8", errors="ignore")
    key = _LOCAL_SIGN_SEED.encode("utf-8", errors="ignore")
    return hmac.new(key, msg, hashlib.sha256).hexdigest()


def _save_last_ok_state(license_key: str, last_ok_unix: int) -> None:
    fp = _machine_fingerprint()
    payload = {
        "last_ok_unix": int(last_ok_unix),
        "fp": fp,
        "sig": _state_sig(license_key, int(last_ok_unix), fp),
    }
    with open(_state_path(), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def _load_last_ok_state(license_key: str) -> int | None:
    sp = _state_path()
    if not os.path.isfile(sp):
        return None
    try:
        with open(sp, encoding="utf-8") as f:
            data = json.load(f)
        last_ok = int(data.get("last_ok_unix") or 0)
        fp = str(data.get("fp") or "")
        sig = str(data.get("sig") or "")
        if not last_ok or not fp or not sig:
            return None
        if fp != _machine_fingerprint():
            return None
        exp = _state_sig(license_key, last_ok, fp)
        if not hmac.compare_digest(sig, exp):
            return None
        return last_ok
    except Exception:
        return None


def _request_status(server_url: str, license_key: str, timeout: float = 12.0) -> tuple[bool, str | None]:
    """
    Llama al servidor. Devuelve (ok, reason) donde reason es None si la licencia está activa;
    si no, uno de: ``inactive``, ``not_found``, ``http_error``, ``network``.
    """
    base = server_url.rstrip("/")
    safe_key = urllib.parse.quote(license_key, safe="")
    url = f"{base}/api/license/{safe_key}/status"
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "VmPOS/1"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            data = json.loads(body)
            if bool(data.get("active")):
                return True, None
            return False, "inactive"
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False, "not_found"
        try:
            body = e.read().decode("utf-8", errors="replace")
            data = json.loads(body)
            if not bool(data.get("active", False)):
                return False, "inactive"
        except Exception:
            pass
        return False, "http_error"
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return False, "network"


def remote_license_screening() -> tuple[bool, str, str]:
    """
    Debe llamarse tras login exitoso y antes de abrir el menú principal.

    Returns:
        (allowed, title, message) — si allowed es False, mostrar mensaje y no continuar.
    """
    cfg = _load_cfg()
    if not cfg:
        if bool(getattr(sys, "frozen", False)):
            return (
                False,
                "Acceso desactivado",
                "No se encontró la configuración de licencia remota.\n\n"
                "Contacte a soporte para renovar o reactivar la licencia.",
            )
        return True, "", ""
    if not bool(cfg.get("remote_check_enabled")):
        # En producción (.exe), la validación remota es obligatoria.
        if bool(getattr(sys, "frozen", False)):
            return (
                False,
                "Acceso desactivado",
                "La validación remota está desactivada en esta instalación.\n\n"
                "Contacte a soporte para renovar o reactivar la licencia.",
            )
        return True, "", ""

    server_url = (cfg.get("server_url") or "").strip()
    license_key = (cfg.get("license_key") or "").strip()
    # Seguridad: no confiar en offline_grace_hours editable por usuario.
    grace_h = OFFLINE_GRACE_HOURS

    if not server_url or not license_key:
        return False, "Configuración de licencia", "Revise license_remote.json: faltan server_url o license_key."

    ok, reason = _request_status(server_url, license_key)

    if ok:
        now_ts = int(time.time())
        cfg["last_ok_unix"] = now_ts
        try:
            _save_cfg(cfg)
        except OSError:
            pass
        try:
            _save_last_ok_state(license_key, now_ts)
        except OSError:
            pass
        return True, "", ""

    if reason in ("inactive", "not_found"):
        return (
            False,
            "Licencia bloqueada",
            "Esta instalación no está autorizada en el servidor de licencias.\n\n"
            "Contacte al administrador o verifique la clave en license_remote.json.",
        )

    # Red / timeout: período de gracia basado en estado firmado local.
    # Se ignora last_ok_unix del JSON para evitar bypass por edición manual.
    last_ok = _load_last_ok_state(license_key)
    if isinstance(last_ok, int) and last_ok > 0:
        elapsed = time.time() - float(last_ok)
        if elapsed <= grace_h * 3600:
            return True, "", ""

    return (
        False,
        "Sin conexión con el servidor de licencias",
        "No se pudo verificar el acceso y ya venció el período de gracia sin conexión.\n\n"
        "Compruebe internet y la URL del servidor, o contacte a soporte.",
    )
