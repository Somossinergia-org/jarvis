"""Servidor principal de Jarvis."""
import os
import sys
import asyncio

# Forzar UTF-8 en stdout/stderr para que los emojis no revienten en Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import PORT, HOST, AUDIO_CACHE_DIR
from brain import JarvisBrain
from tts_engine import text_to_speech, list_spanish_voices, clean_cache
from plugins.system_plugin import get_system_info, get_datetime_info, open_application, open_url
from plugins.productivity_plugin import (
    add_task, list_tasks, complete_task, delete_task,
    add_note, list_notes, search_notes,
)


# --- Instancia del cerebro ---
jarvis = JarvisBrain()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicialización y limpieza del servidor."""
    print("\n" + "=" * 55)
    print("  ✨  J.A.R.V.I.S. en línea  ✨")
    print(f"  🌐  http://localhost:{PORT}")
    print("  🎤  Reconocimiento de voz: activado")
    print("  🔊  Síntesis de voz: activado")
    print("  🧠  Motor: OpenAI GPT-4o")
    print("=" * 55 + "\n")
    yield
    print("\n⚡ JARVIS desconectado. Hasta pronto, señor.\n")


app = FastAPI(
    title="JARVIS - Asistente Personal IA",
    version="1.0.0",
    lifespan=lifespan,
)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/audio", StaticFiles(directory=AUDIO_CACHE_DIR), name="audio")


# --- Modelos de datos ---
class ChatMessage(BaseModel):
    message: str
    is_voice: bool = False
    speak_response: bool = False
    voice: str | None = None


class TaskRequest(BaseModel):
    title: str
    priority: str = "media"


class NoteRequest(BaseModel):
    title: str
    content: str


# --- Rutas principales ---
@app.get("/", response_class=HTMLResponse)
async def home():
    """Página principal de Jarvis."""
    with open(os.path.join("static", "index.html"), "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.post("/api/chat")
async def chat(msg: ChatMessage):
    """Endpoint principal de conversación."""
    response_text = await jarvis.think(msg.message, is_voice=msg.is_voice)

    result = {
        "response": response_text,
        "audio_url": None,
    }

    # Generar audio si se pide
    if msg.speak_response:
        try:
            audio_path = await text_to_speech(response_text, msg.voice)
            filename = os.path.basename(audio_path)
            result["audio_url"] = f"/audio/{filename}"
        except Exception as e:
            result["tts_error"] = str(e)

    # Limpiar caché periódicamente
    clean_cache()

    return JSONResponse(result)


@app.post("/api/clear")
async def clear_history():
    """Limpia el historial de conversación."""
    msg = jarvis.clear_history()
    return {"message": msg}


@app.get("/api/stats")
async def stats():
    """Estadísticas de la sesión."""
    return jarvis.get_stats()


@app.get("/api/system")
async def system_info():
    """Información del sistema."""
    return get_system_info()


@app.get("/api/datetime")
async def datetime_info():
    """Fecha y hora actual."""
    return get_datetime_info()


@app.post("/api/open/app")
async def launch_app(req: dict):
    """Abre una aplicación del sistema."""
    app_name = req.get("app", "")
    if not app_name:
        return JSONResponse({"error": "Falta el campo 'app'"}, status_code=400)
    return {"message": open_application(app_name)}


@app.post("/api/open/url")
async def launch_url(req: dict):
    """Abre una URL en el navegador por defecto."""
    url = req.get("url", "")
    if not url:
        return JSONResponse({"error": "Falta el campo 'url'"}, status_code=400)
    return {"message": open_url(url)}


@app.get("/api/voices")
async def voices():
    """Lista voces españolas disponibles."""
    return await list_spanish_voices()


# --- Memoria persistente ---
@app.get("/api/memory")
async def get_memory():
    """Devuelve la memoria persistente de JARVIS."""
    from plugins.memory_plugin import load_recent_memory, get_memory_stats
    return {
        "stats": get_memory_stats(),
        "entries": load_recent_memory(n=50),
    }


@app.delete("/api/memory")
async def delete_memory():
    """Borra la memoria persistente de JARVIS."""
    from plugins.memory_plugin import clear_memory
    return {"message": clear_memory()}



# --- Tareas ---
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


# --- Notas ---
@app.post("/api/notes")
async def create_note(req: NoteRequest):
    return add_note(req.title, req.content)


@app.get("/api/notes")
async def get_notes():
    return list_notes()


@app.get("/api/notes/search")
async def find_notes(q: str):
    return search_notes(q)


# --- Arranque ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host=HOST, port=PORT, reload=True)
