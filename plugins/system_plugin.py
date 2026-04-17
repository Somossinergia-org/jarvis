"""
plugins/system_plugin.py — Control TOTAL del sistema Windows para JARVIS v4.0
"""
import os
import sys
import platform
import subprocess
import psutil
from datetime import datetime


# ── Mapa de aplicaciones conocidas ────────────────────────────────────
APP_MAP = {
    "chrome":           "chrome",
    "google chrome":    "chrome",
    "firefox":          "firefox",
    "edge":             "msedge",
    "microsoft edge":   "msedge",
    "notepad":          "notepad",
    "bloc de notas":    "notepad",
    "word":             "winword",
    "excel":            "excel",
    "powerpoint":       "powerpnt",
    "spotify":          "spotify",
    "discord":          "discord",
    "telegram":         "telegram",
    "whatsapp":         "WhatsApp",
    "calculadora":      "calc",
    "calculator":       "calc",
    "explorador":       "explorer",
    "explorer":         "explorer",
    "file explorer":    "explorer",
    "administrador de tareas": "taskmgr",
    "task manager":     "taskmgr",
    "panel de control": "control",
    "configuracion":    "ms-settings:",
    "settings":         "ms-settings:",
    "paint":            "mspaint",
    "cmd":              "cmd",
    "consola":          "cmd",
    "powershell":       "powershell",
    "terminal":         "wt",
    "windows terminal": "wt",
    "vlc":              "vlc",
    "zoom":             "zoom",
    "teams":            "teams",
    "outlook":          "outlook",
    "visual studio code": "code",
    "vscode":           "code",
    "steam":            "steam",
    "obs":              "obs64",
    "notepad++":        "notepad++",
    "7zip":             "7zFM",
    "winrar":           "winrar",
    "skype":            "skype",
    "snipping tool":    "SnippingTool",
    "recortes":         "SnippingTool",
}


def open_application(app_name: str) -> dict:
    """Abre cualquier aplicación por nombre."""
    name = app_name.strip().lower()
    cmd = APP_MAP.get(name, app_name)  # si no está en el mapa, intenta con el nombre directo
    try:
        if cmd.startswith("ms-"):
            os.startfile(cmd)
        elif cmd == "spotify":
            # Abre Spotify via URI para que no abra una segunda instancia
            os.startfile("spotify:")
        else:
            subprocess.Popen(cmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return {"status": "ok", "mensaje": f"Abriendo {app_name}..."}
    except FileNotFoundError:
        # Fallback: buscar en Program Files
        for base in [r"C:\Program Files", r"C:\Program Files (x86)", os.path.expanduser("~\\AppData\\Local\\Programs")]:
            for root, dirs, files in os.walk(base):
                for f in files:
                    if app_name.lower() in f.lower() and f.endswith(".exe"):
                        try:
                            subprocess.Popen(os.path.join(root, f), shell=False, creationflags=subprocess.CREATE_NO_WINDOW)
                            return {"status": "ok", "mensaje": f"Abriendo {f}"}
                        except Exception:
                            pass
        return {"error": f"No se encontró la aplicación: {app_name}. Prueba con el nombre exacto del ejecutable."}
    except Exception as e:
        return {"error": str(e)}


def close_application(app_name: str) -> dict:
    """Cierra una aplicación por nombre de proceso."""
    killed = []
    for proc in psutil.process_iter(["name", "pid"]):
        try:
            if app_name.lower() in proc.info["name"].lower():
                proc.terminate()
                killed.append(proc.info["name"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    if killed:
        return {"status": "ok", "mensaje": f"Cerradas {len(killed)} instancias: {', '.join(set(killed))}"}
    return {"status": "not_found", "mensaje": f"No se encontró el proceso: {app_name}"}


def execute_command(command: str, use_powershell: bool = True) -> dict:
    """Ejecuta un comando del sistema y devuelve el resultado."""
    try:
        if use_powershell:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                capture_output=True, text=True, timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            result = subprocess.run(
                command, capture_output=True, text=True, timeout=30,
                shell=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
        return {
            "status": "ok" if result.returncode == 0 else "error",
            "stdout": result.stdout[:600].strip() if result.stdout else "",
            "stderr": result.stderr[:200].strip() if result.stderr else "",
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"error": "Timeout: el comando tardó más de 30 segundos."}
    except Exception as e:
        return {"error": str(e)}


def open_url(url: str) -> dict:
    """Abre una URL en el navegador por defecto."""
    try:
        import webbrowser
        if not url.startswith("http"):
            url = "https://" + url
        webbrowser.open(url)
        return {"status": "ok", "mensaje": f"Abriendo {url}"}
    except Exception as e:
        return {"error": str(e)}


def control_volume(action: str = "get", level: int = None) -> dict:
    """Controla el volumen del sistema.
    action: up | down | mute | unmute | set
    level: 0-100 (solo para 'set')
    """
    try:
        wsh_cmd = lambda key: f"$wsh = New-Object -ComObject WScript.Shell; $wsh.SendKeys([char]{key})"
        if action == "up":
            for _ in range(5):
                subprocess.run(["powershell", "-Command", wsh_cmd(175)], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            return {"status": "ok", "mensaje": "Volumen subido"}
        elif action == "down":
            for _ in range(5):
                subprocess.run(["powershell", "-Command", wsh_cmd(174)], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            return {"status": "ok", "mensaje": "Volumen bajado"}
        elif action in ("mute", "unmute"):
            subprocess.run(["powershell", "-Command", wsh_cmd(173)], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            return {"status": "ok", "mensaje": "Volumen silenciado/desilenciado"}
        elif action == "set" and level is not None:
            lvl = max(0, min(100, int(level)))
            # Usando PowerShell + nircmd alternativo con WMI
            ps_script = f"""
$volume = [Math]::Round({lvl} / 100.0, 2)
$obj = New-Object -ComObject WMPlayer.OCX.7
$obj.settings.volume = {lvl}
"""
            subprocess.run(["powershell", "-Command", ps_script], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            return {"status": "ok", "mensaje": f"Volumen ajustado a {lvl}%"}
        else:
            return {"error": "Acción no válida. Usa: up, down, mute, unmute, set"}
    except Exception as e:
        return {"error": str(e)}


def control_media(action: str) -> dict:
    """Controla la reproducción de medios (Spotify, etc.).
    action: play_pause | next | previous | stop
    """
    key_map = {
        "play_pause": 179,
        "next":       176,
        "previous":   177,
        "stop":       178,
    }
    key_code = key_map.get(action, 179)
    try:
        cmd = f"$wsh = New-Object -ComObject WScript.Shell; $wsh.SendKeys([char]{key_code})"
        subprocess.run(["powershell", "-Command", cmd], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return {"status": "ok", "mensaje": f"Acción de media ejecutada: {action}"}
    except Exception as e:
        return {"error": str(e)}


def take_screenshot(filename: str = None) -> dict:
    """Captura la pantalla y la guarda en el escritorio."""
    try:
        from PIL import ImageGrab
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = filename or os.path.join(os.path.expanduser("~"), "Desktop", f"jarvis_{ts}.png")
        img = ImageGrab.grab()
        img.save(path)
        return {"status": "ok", "mensaje": f"Captura guardada: {path}", "ruta": path}
    except ImportError:
        # Fallback: PowerShell
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(os.path.expanduser("~"), "Desktop", f"jarvis_{ts}.png")
        ps = f"""
Add-Type -AssemblyName System.Windows.Forms,System.Drawing
$bmp = New-Object System.Drawing.Bitmap([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width, [System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen(0,0,0,0,$bmp.Size)
$bmp.Save('{path}')
"""
        result = subprocess.run(["powershell", "-Command", ps], capture_output=True, timeout=10)
        if os.path.exists(path):
            return {"status": "ok", "mensaje": f"Captura guardada: {path}", "ruta": path}
        return {"error": "No se pudo tomar la captura"}
    except Exception as e:
        return {"error": str(e)}


def type_text_at_cursor(text: str) -> dict:
    """Escribe texto en la posición actual del cursor."""
    try:
        import pyautogui
        pyautogui.write(text, interval=0.02)
        return {"status": "ok", "mensaje": f"Texto escrito: {text[:40]}..."}
    except ImportError:
        # Fallback PowerShell
        safe_text = text.replace("'", "''").replace("{", "{{").replace("}", "}}")
        ps = f"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('{safe_text}')"
        subprocess.run(["powershell", "-Command", ps], capture_output=True)
        return {"status": "ok", "mensaje": f"Texto enviado: {text[:40]}..."}
    except Exception as e:
        return {"error": str(e)}


def press_key(key: str) -> dict:
    """Simula la pulsación de una tecla (enter, escape, f5, ctrl+c, etc.)."""
    try:
        import pyautogui
        # Convertir atajos comunes
        key_map = {
            "enter": "enter", "escape": "esc", "esc": "esc",
            "tab": "tab", "espacio": "space", "space": "space",
            "inicio": "home", "fin": "end", "home": "home", "end": "end",
            "subir": "pageup", "bajar": "pagedown",
        }
        k = key_map.get(key.lower(), key.lower())
        if "+" in k:
            parts = k.split("+")
            pyautogui.hotkey(*parts)
        else:
            pyautogui.press(k)
        return {"status": "ok", "mensaje": f"Tecla pulsada: {key}"}
    except ImportError:
        return {"status": "ok", "mensaje": "pyautogui no disponible, intenta con execute_command"}
    except Exception as e:
        return {"error": str(e)}


def list_running_apps() -> dict:
    """Lista las aplicaciones actualmente en ejecución."""
    try:
        apps = {}
        for proc in psutil.process_iter(["name", "pid", "memory_info"]):
            try:
                name = proc.info["name"]
                if name and ".exe" in name.lower() and name not in apps:
                    apps[name] = proc.info["pid"]
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        # Ordenar por nombre y devolver los primeros 20
        sorted_apps = sorted(apps.keys())[:20]
        return {"aplicaciones_activas": sorted_apps, "total": len(apps)}
    except Exception as e:
        return {"error": str(e)}


# ── Información del sistema (ya existía) ──────────────────────────────
def get_system_info() -> dict:
    """CPU, RAM, disco en tiempo real."""
    info = {
        "cpu_uso_porcentaje": psutil.cpu_percent(interval=0.5),
        "cpu_nucleos": psutil.cpu_count(),
        "ram_total_gb": round(psutil.virtual_memory().total / 1e9, 1),
        "ram_uso_porcentaje": psutil.virtual_memory().percent,
        "ram_disponible_gb": round(psutil.virtual_memory().available / 1e9, 1),
    }
    try:
        disk_path = "C:\\" if platform.system() == "Windows" else "/"
        disk = psutil.disk_usage(disk_path)
        info["disco_total_gb"] = round(disk.total / 1e9, 1)
        info["disco_uso_porcentaje"] = disk.percent
        info["disco_libre_gb"] = round(disk.free / 1e9, 1)
    except Exception:
        pass
    return info


def get_datetime_info() -> dict:
    """Fecha y hora actual."""
    now = datetime.now()
    return {
        "fecha": now.strftime("%A, %d de %B de %Y"),
        "hora": now.strftime("%H:%M:%S"),
        "timestamp": now.isoformat(),
    }
