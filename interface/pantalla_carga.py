#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pantalla de carga optimizada para Sistema VM
Archivo: interface/pantalla_carga.py
"""

import tkinter as tk
import math
import threading
import sys
import os
import platform
import base64
import subprocess
import shutil

from layout_responsive import centrar_ventana
from ui_theme import T, F_BODY, F_SMALL, F_SUB, FONT

# Configuración de rutas para PyInstaller
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# pyttsx3: respaldo (Linux, o Windows si SAPI vía win32com falla)
try:
    import pyttsx3
    TTS_PYTTSX3 = True
except ImportError:
    TTS_PYTTSX3 = False

# win32: motor principal de voz en Windows (SAPI) — distinto a pyttsx3
TTS_SAPI_W32 = False
if platform.system() == "Windows":
    try:
        import win32com.client  # noqa: F401
        TTS_SAPI_W32 = True
    except ImportError:
        pass


def _sapi_seleccionar_espanol(sp) -> None:
    try:
        toks = sp.GetVoices()
        for i in range(int(toks.Count)):
            t = toks.Item(i)
            d = (t.GetDescription() or "")
            d_low = d.lower()
            if any(
                s in d_low
                for s in (
                    "spanish",
                    "español",
                    "es-mx",
                    "es-es",
                    "mexic",
                    "sabina",
                    "helena",
                    "laura",
                    "pablo",
                )
            ) and "catal" not in d_low:
                sp.Voice = t
                return
    except Exception:
        pass


def _reproducir_bienvenida_sapi_win32(nombre_real: str) -> bool:
    """
    SAPI (Speech API) vía pywin32: suele funcionar aunque pyttsx3 falle.
    Debe llamarse desde un hilo con CoInitialize, luego CoUninitialize.
    """
    if not TTS_SAPI_W32:
        return False
    import pythoncom
    import win32com.client  # type: ignore

    texto = f"Bienvenido {nombre_real}, sistema listo"
    com_ok = False
    try:
        pythoncom.CoInitialize()
        com_ok = True
        sp = win32com.client.Dispatch("SAPI.SpVoice")
        sp.Rate = 0
        sp.Volume = 90
        try:
            _sapi_seleccionar_espanol(sp)
        except Exception as exv:
            print(f"VmPOS: voz SAPI (idioma) — se usa la predeterminada: {exv}")
        # 0 = hablar y esperar a terminar (fiable; corre en hilo separado, no congela Tk)
        sp.Speak(texto, 0)
        return True
    except Exception as e:
        print(f"VmPOS: SAPI no pudo hablar: {e}")
        return False
    finally:
        if com_ok:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass


def _reproducir_bienvenida_sapi_hilo_ui(nombre_real: str) -> bool:
    """
    SAPI en el hilo de Tk: Speak asíncrono (1) = no congela la animación.
    """
    if not TTS_SAPI_W32:
        return False
    try:
        import win32com.client  # type: ignore

        texto = f"Bienvenido {nombre_real}, sistema listo"
        sp = win32com.client.Dispatch("SAPI.SpVoice")
        sp.Rate = 0
        sp.Volume = 90
        _sapi_seleccionar_espanol(sp)
        # 1 = SVSFlagsAsync: encola y devuelve de inmediato
        sp.Speak(texto, 1)
        return True
    except Exception as e:
        print(f"VmPOS: SAPI hilo de interfaz: {e}")
        return False


def _reproducir_bienvenida_pyttsx3(nombre_real: str) -> bool:
    if not TTS_PYTTSX3:
        return False
    com_inicializado = False
    try:
        if platform.system() == "Windows":
            import pythoncom
            # Apartamento hilo: más compatible con pyttsx3 en segundo plano
            try:
                pythoncom.CoInitializeEx(pythoncom.COINIT_APARTMENTTHREADED)
            except (AttributeError, Exception):
                pythoncom.CoInitialize()
            com_inicializado = True
        import pyttsx3
        try:
            engine = pyttsx3.init("sapi5")
        except Exception:
            engine = pyttsx3.init()
        engine.setProperty("rate", 150)
        engine.setProperty("volume", 0.9)
        try:
            for v in engine.getProperty("voices") or []:
                n = (getattr(v, "name", "") or "").lower()
                if any(
                    s in n
                    for s in (
                        "spanish",
                        "español",
                        "sabina",
                        "helena",
                        "laura",
                    )
                ):
                    engine.setProperty("voice", v.id)
                    break
        except Exception:
            pass
        msg = f"Bienvenido {nombre_real}, sistema listo"
        engine.say(msg)
        engine.runAndWait()
        return True
    except Exception as e:
        print(f"VmPOS: pyttsx3: {e}")
        return False
    finally:
        if com_inicializado:
            try:
                import pythoncom
                pythoncom.CoUninitialize()
            except Exception:
                pass


def _ruta_powershell() -> str:
    c = os.path.join(
        os.environ.get("SystemRoot", r"C:\Windows"),
        "System32",
        "WindowsPowerShell",
        "v1.0",
        "powershell.exe",
    )
    if os.path.isfile(c):
        return c
    w = shutil.which("powershell.exe")
    if w:
        return w
    w2 = shutil.which("pwsh.exe")
    return w2 or "powershell.exe"


def _reproducir_bienvenida_powershell(nombre: str) -> bool:
    """
    Usa .NET System.Speech en un proceso separado. Suele oírse aunque win32com/pyttsx3 fallen.
    """
    if platform.system() != "Windows":
        return False
    msg = f"Bienvenido {nombre},  EL sistema esta listo"
    try:
        b64 = base64.b64encode(msg.encode("utf-8")).decode("ascii")
    except Exception:
        return False
    # -EncodedCommand (UTF-16LE) evita que -Command falle por parsing/escape; MS lo usa para invocar PS desde otros procesos
    linea = (
        f"$ProgressPreference='SilentlyContinue';"
        f"$b=[System.Convert]::FromBase64String('{b64}');"
        f"$t=[System.Text.Encoding]::UTF8.GetString($b);"
        f"Add-Type -AssemblyName System.Speech;"
        f"$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;"
        f"$s.Speak($t)"
    )
    try:
        linea_b64 = base64.b64encode(linea.encode("utf-16-le")).decode("ascii")
    except Exception:
        return False
    pw = _ruta_powershell()
    try:
        creationflags = 0
        if sys.platform == "win32" and hasattr(subprocess, "CREATE_NO_WINDOW"):
            creationflags = subprocess.CREATE_NO_WINDOW
        r = subprocess.run(
            [
                pw,
                "-NoProfile",
                "-NonInteractive",
                "-NoLogo",
                "-ExecutionPolicy",
                "Bypass",
                "-EncodedCommand",
                linea_b64,
            ],
            capture_output=True,
            text=True,
            timeout=60,
            creationflags=creationflags,
        )
        if r.returncode == 0:
            return True
        err = (r.stderr or "") + (r.stdout or "")
        print(f"VmPOS: PowerShell TTS codigo {r.returncode}: {err[:500]}")
    except FileNotFoundError:
        print("VmPOS: no se encontro powershell.exe")
    except subprocess.TimeoutExpired:
        print("VmPOS: PowerShell TTS excedio el tiempo de espera")
    except Exception as e:
        print(f"VmPOS: PowerShell TTS: {e}")
    return False


def _bienvenida_todas_motores(nombre: str) -> None:
    """
    Hilo: primero PowerShell (mas fiable en Windows), luego SAPI/pywin32, luego pyttsx3.
    """
    if platform.system() == "Windows":
        if _reproducir_bienvenida_powershell(nombre):
            return
    if TTS_SAPI_W32 and _reproducir_bienvenida_sapi_win32(nombre):
        return
    if TTS_PYTTSX3 and _reproducir_bienvenida_pyttsx3(nombre):
        return
    if platform.system() == "Windows":
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass
    print("VmPOS: voz: ningun motor pudo leer en voz alta (revisa voz/altavoces de Windows).")


def _hilo_bienvenida_respaldo(nombre_real: str) -> None:
    """Mantenido para compat; delega a la misma logica completa."""
    _bienvenida_todas_motores(nombre_real)


def mostrar_carga(nombre="Usuario", usuario_info=None):
    """
    Muestra una pantalla de carga optimizada (más rápida)
    Args:
        nombre (str): Nombre del usuario (se usará como fallback si no hay usuario_info)
        usuario_info (dict): Información completa del usuario (con claves 'usuario' y 'permisos')
    """
    
    # Determinar el nombre real del usuario
    if usuario_info and 'usuario' in usuario_info:
        nombre_real = usuario_info['usuario']
    else:
        nombre_real = nombre
    
    ventana = tk.Tk()
    ventana.title(f"VmPOS — {nombre_real}")
    ventana.configure(bg=T.SPLASH_OUTER)
    ventana.resizable(False, False)
    ventana.overrideredirect(True)
    centrar_ventana(ventana, 550, 350)

    main_frame = tk.Frame(ventana, bg=T.SPLASH_CARD, width=530, height=330, highlightbackground=T.BORDER, highlightthickness=1)
    main_frame.place(relx=0.5, rely=0.5, anchor="center")
    main_frame.pack_propagate(False)

    header_frame = tk.Frame(main_frame, bg=T.SPLASH_HEADER, height=56)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)

    icons_frame = tk.Frame(header_frame, bg=T.SPLASH_HEADER)
    icons_frame.pack(expand=True)

    icons = ["·", "◆", "·"]
    icon_labels = []
    for i, icon in enumerate(icons):
        label = tk.Label(icons_frame, text=icon, font=(FONT, 14), bg=T.SPLASH_HEADER, fg=T.HEADER_TEXT_DIM)
        label.grid(row=0, column=i, padx=20, pady=14)
        icon_labels.append(label)

    user_info_frame = tk.Frame(main_frame, bg=T.SPLASH_BODY)
    user_info_frame.pack(pady=15)

    if usuario_info:
        # Corrección: se usan las claves correctas 'usuario' y 'permisos'
        nombre_usuario = usuario_info.get('usuario', nombre_real)
        permisos_usuario = usuario_info.get('rol_completo', usuario_info.get('permisos', 'No definido'))

        tk.Label(
            user_info_frame,
            text=f"Hola, {nombre_usuario.capitalize()}",
            font=(FONT, 18, "bold"),
            bg=T.SPLASH_BODY,
            fg=T.TEXT,
        ).pack()

        tk.Label(
            user_info_frame,
            text=f"Rol: {permisos_usuario}",
            font=F_BODY,
            bg=T.SPLASH_BODY,
            fg=T.TEXT_MUTED,
        ).pack()

        tk.Label(
            user_info_frame,
            text="Cargando aplicación…",
            font=F_BODY,
            bg=T.SPLASH_BODY,
            fg=T.TEXT_MUTED,
        ).pack(pady=(8, 0))
    else:
        tk.Label(
            user_info_frame,
            text=f"Hola, {nombre_real}",
            font=(FONT, 18, "bold"),
            bg=T.SPLASH_BODY,
            fg=T.TEXT,
        ).pack()

        tk.Label(
            user_info_frame,
            text="Cargando aplicación…",
            font=F_BODY,
            bg=T.SPLASH_BODY,
            fg=T.TEXT_MUTED,
        ).pack(pady=(8, 0))

    # Loader circular más pequeño y rápido
    loader_frame = tk.Frame(main_frame, bg=T.SPLASH_BODY, width=100, height=100)
    loader_frame.pack(pady=15)
    loader_frame.pack_propagate(False)

    canvas = tk.Canvas(loader_frame, width=80, height=80, bg=T.SPLASH_BODY, highlightthickness=0)
    canvas.place(relx=0.5, rely=0.5, anchor="center")

    # Círculos del loader (menos para mejor rendimiento)
    circles = []
    center_x, center_y = 40, 40
    radius = 25
    
    for i in range(8):  # Reducido de 12 a 8
        angle = i * (360 / 8)
        x = center_x + radius * math.cos(math.radians(angle))
        y = center_y + radius * math.sin(math.radians(angle))
        
        circle = canvas.create_oval(x-3, y-3, x+3, y+3, fill="#cbd5e1", outline="", width=0)
        circles.append(circle)

    # Barra de progreso más pequeña
    progress_frame = tk.Frame(main_frame, bg=T.SPLASH_BODY)
    progress_frame.pack(pady=10, padx=40, fill="x")

    progress_bg = tk.Frame(progress_frame, bg=T.DIVIDER, height=4)
    progress_bg.pack(fill="x")

    progress_bar = tk.Frame(progress_bg, bg=T.ACCENT, height=4, width=0)
    progress_bar.pack(side="left")

    # Estado de carga
    status_label = tk.Label(main_frame, text="Preparando…", font=F_BODY, bg=T.SPLASH_BODY, fg=T.TEXT_MUTED)
    status_label.pack(pady=5)

    # Footer compacto
    footer_frame = tk.Frame(main_frame, bg=T.SPLASH_HEADER, height=40)
    footer_frame.pack(side="bottom", fill="x")
    footer_frame.pack_propagate(False)

    tk.Label(
        footer_frame,
        text="VmPOS · Centro de copiado y papelería",
        font=F_SMALL,
        bg=T.SPLASH_HEADER,
        fg=T.HEADER_TEXT_DIM,
    ).pack(pady=10)

    def _reproducir_bienvenida() -> None:
        threading.Thread(
            target=_bienvenida_todas_motores,
            args=(nombre_real,),
            daemon=True,
            name="VmPOS-Bienvenida",
        ).start()

    ventana.after(500, _reproducir_bienvenida)

    # Variables de animación (optimizadas)
    progress_width = 0
    max_width = 470  # Ancho máximo ajustado
    
    # Mensajes de estado reducidos
    status_messages = [
        "Iniciando... 🚀",
        "Cargando datos... 📊", 
        "Preparando interfaz... 🖥️",
        "Sistema listo... ✨"
    ]

    def animar_iconos(indice=0):
        """Animación de iconos más rápida"""
        try:
            for i, label in enumerate(icon_labels):
                if i == indice % len(icon_labels):
                    label.config(font=("Segoe UI Emoji", 20))
                else:
                    label.config(font=("Segoe UI Emoji", 16))
            
            if ventana.winfo_exists():
                ventana.after(400, lambda: animar_iconos(indice + 1))
        except tk.TclError:
            # La ventana ya fue destruida
            pass

    # Animación mucho más rápida
    total_cycles = 20  # Reducido drásticamente de 48 a 20
    
    def animar_loader(indice=0, ciclos=0):
        nonlocal progress_width
        
        try:
            if ciclos < total_cycles and ventana.winfo_exists():
                # Animar círculos del loader
                for i, circle in enumerate(circles):
                    if i == indice:
                        canvas.itemconfig(circle, fill="#be185d")
                    elif i == (indice - 1) % 8:
                        canvas.itemconfig(circle, fill="#64748b")
                    else:
                        canvas.itemconfig(circle, fill="#cbd5e1")
                
                # Animar barra de progreso
                progress_width = (ciclos / (total_cycles - 1)) * max_width
                progress_bar.config(width=int(progress_width))
                
                # Cambiar mensaje de estado
                message_index = min(ciclos // (total_cycles // len(status_messages)), len(status_messages) - 1)
                status_label.config(text=status_messages[message_index])
                
                ventana.update()
                ventana.after(50, lambda: animar_loader((indice + 1) % 8, ciclos + 1))  # Muy rápido
            elif ventana.winfo_exists():
                # Finalizar
                status_label.config(text="¡Listo! 🎉")
                progress_bar.config(width=max_width, bg="#059669")
                ventana.update()
                ventana.after(200, ventana.destroy)  # Cerrar rápidamente
        except tk.TclError:
            # La ventana ya fue destruida
            pass

    # Iniciar animaciones
    ventana.after(100, animar_iconos)
    ventana.after(100, animar_loader)
    
    # Auto-cerrar por seguridad (por si algo falla)
    ventana.after(3000, lambda: ventana.destroy() if ventana.winfo_exists() else None)
    
    try:
        ventana.mainloop()
    except tk.TclError:
        # La ventana ya fue destruida
        pass
    
    # Retornar referencia a la ventana para compatibilidad
    return ventana

# Función de prueba
if __name__ == "__main__":
    # Simular información de usuario
    usuario_test = {
        'usuario': 'Prueba',
        'permisos': 'administrador',
        'rol_completo': 'Administrador'
    }
    mostrar_carga("pruba", usuario_test)
    
