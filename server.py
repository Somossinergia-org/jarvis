"""Servidor principal de JARVIS v5.0."""
import os
import sys
import json

# UTF-8 para emojis en Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import PORT, HOST, AUDIO_CACHE_DIR
from brain import JarvisBrain
from tts_engine import text_to_speech, list_spanish_voices, clean_cache
from plugins.system_plugin import (
    get_system_info, get_datetime_info, open_application, open_url,
    control_volume, control_media
)
from plugins.productivity_plugin import (
    add_task, list_tasks, complete_task, delete_task,
    add_note as prod_add_note,
    list_notes as prod_list_notes,
    search_notes as prod_search_notes,
)
from plugins.vault_plugin import (
    init_vault,
    create_note  as vault_create_note,
    get_note     as vault_get_note,
    update_note  as vault_update_note,
    delete_note  as vault_delete_note,
    list_notes   as vault_list,
    search_notes as vault_search,
    get_graph, get_daily_note, reindex_vault, get_stats as vault_stats,
)

jarvis = JarvisBrain()

# Inicializar bóveda al arrancar
_vault_path = init_vault()
print(f"  [Vault] Bóveda activa: {_vault_path}")



@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "=" * 55)
    print("  J.A.R.V.I.S. v4.0 ULTRA -- Online")
    print(f"  http://localhost:{PORT}")
    print("  Tool Calling: ON | Air Mouse: ON | Face ID: ON")
    print("=" * 55 + "\n")
    yield
    print("\nJARVIS desconectado. Hasta pronto, senor.\n")


app = FastAPI(title="JARVIS v4.0 ULTRA", version="4.0.0", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/audio", StaticFiles(directory=AUDIO_CACHE_DIR), name="audio")


# -- Modelos ---
class ChatMessage(BaseModel):
    message: str
    is_voice: bool = False
    speak_response: bool = False
    voice: str | None = None

class TTSRequest(BaseModel):
    text: str
    voice: str = "onyx"

class TaskRequest(BaseModel):
    title: str
    priority: str = "media"

class NoteRequest(BaseModel):
    title: str
    content: str

class MouseAction(BaseModel):
    action: str
    x: float | None = None
    y: float | None = None
    amount: int = 0


# -- Rutas principales ---
@app.get("/", response_class=HTMLResponse)
async def home():
    with open(os.path.join("static", "index.html"), "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.post("/api/chat")
async def chat(msg: ChatMessage):
    response_text = await jarvis.think(msg.message, is_voice=msg.is_voice)
    result = {"response": response_text, "audio_url": None}
    if msg.speak_response:
        try:
            audio_path = await text_to_speech(response_text, msg.voice)
            filename = os.path.basename(audio_path)
            result["audio_url"] = f"/audio/{filename}"
        except Exception as e:
            result["tts_error"] = str(e)
    clean_cache()
    return JSONResponse(result)


@app.post("/api/tts")
async def tts_direct(req: TTSRequest):
    try:
        audio_path = await text_to_speech(req.text, req.voice)
        with open(audio_path, "rb") as f:
            audio_data = f.read()
        return Response(content=audio_data, media_type="audio/mpeg",
                        headers={"Cache-Control": "no-cache"})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/clear")
async def clear_history():
    return {"message": jarvis.clear_history()}


@app.get("/api/stats")
async def stats():
    return jarvis.get_stats()


@app.get("/api/system")
async def system_info():
    return get_system_info()


@app.get("/api/system/extended")
async def system_extended():
    """Telemetría completa: CPU, RAM, Disco, Red, Procesos, Uptime, Temp."""
    import psutil, time, platform
    try:
        # Base
        cpu  = psutil.cpu_percent(interval=0.3)
        ram  = psutil.virtual_memory().percent
        disk = psutil.disk_usage("C:\\").percent if platform.system()=="Windows" else psutil.disk_usage("/").percent

        # Network I/O (delta since last call)
        net = psutil.net_io_counters()
        def _fmt(b):
            if b < 1024: return f"{b}B/s"
            if b < 1048576: return f"{b//1024}KB/s"
            return f"{b//1048576}MB/s"
        # Use per-second snapshot (quick 0.3s interval already used for CPU)
        net2 = psutil.net_io_counters()
        up_bps = max(0, net2.bytes_sent - net.bytes_sent)
        dn_bps = max(0, net2.bytes_recv - net.bytes_recv)

        # Processes
        procs = len(psutil.pids())

        # Uptime
        boot = psutil.boot_time()
        up_s = int(time.time() - boot)
        h, m = divmod(up_s // 60, 60)
        uptime = f"{h}h {m}m"

        # Temperature (if available)
        temp = "--"
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for k, v in temps.items():
                    if v:
                        temp = f"{v[0].current:.0f}°C"
                        break
        except Exception:
            pass

        return {
            "cpu": cpu, "ram": ram, "disk": disk,
            "net_up": _fmt(up_bps), "net_dn": _fmt(dn_bps),
            "procs": procs, "uptime": uptime, "temp": temp,
            # Also include old keys for compatibility
            "cpu_uso_porcentaje": cpu, "ram_uso_porcentaje": ram, "disco_uso_porcentaje": disk,
        }
    except Exception as e:
        return {"error": str(e), "cpu": 0, "ram": 0, "disk": 0,
                "net_up": "--", "net_dn": "--", "procs": 0, "uptime": "--", "temp": "--"}


@app.get("/api/datetime")
async def datetime_info():
    return get_datetime_info()


# -- Control de sistema directo (para gestos) ---
@app.post("/api/system/volume")
async def sys_volume(req: dict):
    return control_volume(req.get("action", "get"), req.get("level"))

@app.post("/api/system/media")
async def sys_media(req: dict):
    action = req.get("action", "play_pause")
    result = control_media(action)
    if action == "play_pause":
        try:
            import subprocess
            subprocess.Popen(
                ["powershell", "-WindowStyle", "Hidden", "-Command",
                 "$spotify = Get-Process -Name Spotify -ErrorAction SilentlyContinue; "
                 "if ($spotify) { "
                 "  Add-Type -AssemblyName Microsoft.VisualBasic; "
                 "  [Microsoft.VisualBasic.Interaction]::AppActivate($spotify.Id); "
                 "  Start-Sleep -Milliseconds 300; "
                 "  $s = New-Object -ComObject WScript.Shell; "
                 "  $s.SendKeys(' '); "
                 "}"],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        except Exception:
            pass
    return result

@app.post("/api/system/mouse")
async def sys_mouse(req: MouseAction):
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        if req.action == "move" and req.x is not None and req.y is not None:
            pyautogui.moveTo(int(req.x), int(req.y), duration=0)
        elif req.action == "click":
            pyautogui.click()
        elif req.action == "right_click":
            pyautogui.rightClick()
        elif req.action == "double_click":
            pyautogui.doubleClick()
        elif req.action == "scroll":
            pyautogui.scroll(req.amount)
        return {"status": "ok"}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# -- WebSocket: Air Mouse en tiempo real ---
@app.websocket("/ws/hands")
async def websocket_hands(ws: WebSocket):
    await ws.accept()
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        print("  [Air Mouse] WebSocket conectado")
        while True:
            raw = await ws.receive_text()
            data = json.loads(raw)
            action = data.get("action")
            x = data.get("x")
            y = data.get("y")
            try:
                if action == "move" and x is not None and y is not None:
                    pyautogui.moveTo(int(x), int(y), duration=0)
                elif action == "click":
                    pyautogui.click()
                elif action == "right_click":
                    pyautogui.rightClick()
                elif action == "double_click":
                    pyautogui.doubleClick()
                elif action == "scroll_up":
                    pyautogui.scroll(3)
                elif action == "scroll_down":
                    pyautogui.scroll(-3)
                elif action == "open_app":
                    open_application(data.get("app", ""))
            except Exception:
                pass
            await ws.send_text('{"ok":1}')
    except WebSocketDisconnect:
        print("  [Air Mouse] WebSocket desconectado")
    except Exception as e:
        print(f"  [Air Mouse] Error: {e}")


# -- Apps / URLs ---
@app.post("/api/open/app")
async def launch_app(req: dict):
    app_name = req.get("app", "")
    if not app_name:
        return JSONResponse({"error": "Falta el campo 'app'"}, status_code=400)
    return {"message": open_application(app_name)}


@app.post("/api/open/url")
async def launch_url(req: dict):
    url = req.get("url", "")
    if not url:
        return JSONResponse({"error": "Falta el campo 'url'"}, status_code=400)
    return {"message": open_url(url)}




@app.post("/api/open/path")
async def launch_path(req: dict):
    """Abre una carpeta del sistema en el explorador."""
    import subprocess, os
    folder = req.get("path", "Desktop")
    folder_map = {
        "Desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
        "Downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
        "Documents": os.path.join(os.path.expanduser("~"), "Documents"),
        "Pictures": os.path.join(os.path.expanduser("~"), "Pictures"),
    }
    path = folder_map.get(folder, os.path.expanduser("~"))
    try:
        subprocess.Popen(["explorer", path])
        return {"message": f"Abriendo {folder}"}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)



@app.post("/api/auth/startup")
async def auth_startup():
    """Startup biometrico: Spotify play via VK_MEDIA_PLAY_PAUSE + VS Code."""
    import asyncio, ctypes, time as _t

    async def _run():
        # 1. Abrir Spotify
        open_application("spotify")
        await asyncio.sleep(2.0)
        # 2. Play global via media key (sin necesitar foco en Spotify)
        try:
            u32 = ctypes.windll.user32
            u32.keybd_event(0xB3, 0, 0, 0)   # VK_MEDIA_PLAY_PAUSE down
            _t.sleep(0.08)
            u32.keybd_event(0xB3, 0, 2, 0)   # key up
            print("[Startup] PLAY via media key: OK")
        except Exception as ex:
            print(f"[Startup] media key: {ex}")
        # 3. VS Code
        await asyncio.sleep(0.6)
        open_application("code")
        print("[Startup] Secuencia OK")

    asyncio.create_task(_run())
    return {"message": "OK"}


@app.get("/api/files/list")
async def list_files(path: str = "~"):
    """Lista el contenido real de cualquier directorio del sistema."""
    import pathlib as pl
    try:
        clean = path.replace("/", chr(92))
        p = pl.Path(clean).expanduser().resolve()
        if not p.exists():
            return JSONResponse({"error": f"No existe: {p}"}, status_code=404)
        items = []
        try:
            for item in sorted(p.iterdir(),
                               key=lambda x: (not x.is_dir(), x.name.lower())):
                try:
                    st = item.stat()
                    items.append({
                        "name":   item.name,
                        "path":   str(item).replace(chr(92), "/"),
                        "is_dir": item.is_dir(),
                        "size":   st.st_size if item.is_file() else None,
                    })
                except (PermissionError, OSError):
                    pass
        except PermissionError:
            return JSONResponse({"error": "Sin permisos"}, status_code=403)
        return {
            "path":   str(p).replace(chr(92), "/"),
            "parent": str(p.parent).replace(chr(92), "/"),
            "name":   p.name or str(p),
            "items":  items[:150],
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/files/open")
async def open_file_ep(req: dict):
    """Abre archivo o carpeta con la app predeterminada de Windows."""
    import subprocess, pathlib as pl, os
    raw = req.get("path", "").replace("/", chr(92))
    try:
        p = pl.Path(raw).resolve()
        if not p.exists():
            return JSONResponse({"error": "No existe"}, status_code=404)
        if p.is_dir():
            subprocess.Popen(["explorer", str(p)])
        else:
            os.startfile(str(p))
        return {"message": f"Abriendo: {p.name}"}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/voices")
async def voices():
    return await list_spanish_voices()


# -- Memoria persistente ---
@app.get("/api/memory")
async def get_memory():
    from plugins.memory_plugin import load_recent_memory, get_memory_stats
    return {"stats": get_memory_stats(), "entries": load_recent_memory(n=50)}

@app.delete("/api/memory")
async def delete_memory():
    from plugins.memory_plugin import clear_memory
    return {"message": clear_memory()}


# -- Tareas ---
@app.post("/api/tasks")
async def create_task(req: TaskRequest):
    return add_task(req.title, req.priority)

@app.get("/api/tasks")
async def get_tasks(show_completed: bool = False):
    return list_tasks(show_completed)

@app.put("/api/tasks/{task_id}/complete")
async def mark_complete(task_id: int):
    return {"message": complete_task(task_id)}

@app.delete("/api/tasks/{task_id}")
async def remove_task(task_id: int):
    return {"message": delete_task(task_id)}


# -- Notas simples (productivity) ---
@app.post("/api/notes")
async def create_simple_note(req: NoteRequest):
    return prod_add_note(req.title, req.content)

@app.get("/api/notes")
async def get_simple_notes():
    return prod_list_notes()

@app.get("/api/notes/search")
async def find_simple_notes(q: str):
    return prod_search_notes(q)


# ══════════════════════════════════════════════════════
# VAULT — Sistema de Conocimiento Personal JARVIS
# ══════════════════════════════════════════════════════
class VaultNoteReq(BaseModel):
    title: str
    content: str = ""
    folder: str = "notas"
    tags: list = []

class VaultUpdateReq(BaseModel):
    content: str

@app.get("/api/vault/stats")
async def vault_stats_ep():
    return vault_stats()

@app.get("/api/vault/graph")
async def vault_graph():
    return get_graph()

@app.get("/api/vault/notes")
async def vault_notes(folder: str = None):
    return vault_list(folder)

@app.get("/api/vault/note/{title:path}")
async def vault_get(title: str):
    return vault_get_note(title)

@app.post("/api/vault/note")
async def vault_create(req: VaultNoteReq):
    return vault_create_note(req.title, req.content, req.folder, req.tags)

@app.put("/api/vault/note/{title:path}")
async def vault_update(title: str, req: VaultUpdateReq):
    return vault_update_note(title, req.content)

@app.delete("/api/vault/note/{title:path}")
async def vault_delete_ep(title: str):
    return vault_delete_note(title)

@app.get("/api/vault/search")
async def vault_search_ep(q: str):
    return vault_search(q)

@app.get("/api/vault/daily")
async def vault_daily():
    return get_daily_note()

@app.post("/api/vault/reindex")
async def vault_reindex():
    return reindex_vault()


# -- Arranque ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host=HOST, port=PORT, reload=True)
