"""Plugin de sistema: información del PC, hora, comandos básicos."""
import platform
import psutil
import subprocess
import os
from datetime import datetime

# Ruta de disco según SO
_DISK_PATH = "C:\\" if platform.system() == "Windows" else "/"


def get_system_info() -> dict:
    """Devuelve información del sistema."""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(_DISK_PATH)
    except Exception:
        cpu_percent = -1
        memory = None
        disk = None

    return {
        "sistema_operativo": f"{platform.system()} {platform.release()}",
        "procesador": platform.processor() or platform.machine(),
        "cpu_uso_porcentaje": cpu_percent,
        "ram_total_gb": round(memory.total / (1024**3), 1) if memory else "N/A",
        "ram_usada_gb": round(memory.used / (1024**3), 1) if memory else "N/A",
        "ram_uso_porcentaje": memory.percent if memory else "N/A",
        "disco_total_gb": round(disk.total / (1024**3), 1) if disk else "N/A",
        "disco_usado_gb": round(disk.used / (1024**3), 1) if disk else "N/A",
        "disco_uso_porcentaje": round(disk.percent, 1) if disk else "N/A",
        "hostname": platform.node(),
        "python_version": platform.python_version(),
    }


def get_datetime_info() -> dict:
    """Devuelve fecha y hora actual con formato legible."""
    now = datetime.now()
    return {
        "fecha": now.strftime("%A %d de %B de %Y"),
        "hora": now.strftime("%H:%M:%S"),
        "timestamp": now.isoformat(),
    }


def open_application(app_name: str) -> str:
    """Abre una aplicación del sistema (solo Windows/Mac/Linux)."""
    system = platform.system()
    try:
        if system == "Windows":
            os.startfile(app_name)
        elif system == "Darwin":
            subprocess.Popen(["open", "-a", app_name])
        else:
            subprocess.Popen([app_name])
        return f"Abriendo {app_name}..."
    except Exception as e:
        return f"No pude abrir {app_name}: {e}"


def open_url(url: str) -> str:
    """Abre una URL en el navegador por defecto."""
    import webbrowser
    try:
        webbrowser.open(url)
        return f"Abriendo {url} en tu navegador..."
    except Exception as e:
        return f"No pude abrir la URL: {e}"
