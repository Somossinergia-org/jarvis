"""Plugin de productividad: tareas, notas, recordatorios."""
import json
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

TASKS_FILE = os.path.join(DATA_DIR, "tasks.json")
NOTES_FILE = os.path.join(DATA_DIR, "notes.json")


def _load_json(filepath: str) -> list:
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_json(filepath: str, data: list):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# --- TAREAS ---
def add_task(title: str, priority: str = "media") -> dict:
    """Añade una nueva tarea."""
    tasks = _load_json(TASKS_FILE)
    task = {
        "id": len(tasks) + 1,
        "titulo": title,
        "prioridad": priority,
        "completada": False,
        "creada": datetime.now().isoformat(),
    }
    tasks.append(task)
    _save_json(TASKS_FILE, tasks)
    return task


def list_tasks(show_completed: bool = False) -> list:
    """Lista las tareas pendientes."""
    tasks = _load_json(TASKS_FILE)
    if not show_completed:
        tasks = [t for t in tasks if not t["completada"]]
    return tasks


def complete_task(task_id: int) -> str:
    """Marca una tarea como completada."""
    tasks = _load_json(TASKS_FILE)
    for task in tasks:
        if task["id"] == task_id:
            task["completada"] = True
            task["completada_en"] = datetime.now().isoformat()
            _save_json(TASKS_FILE, tasks)
            return f"Tarea '{task['titulo']}' completada."
    return f"No encontré la tarea con ID {task_id}."


def delete_task(task_id: int) -> str:
    """Elimina una tarea."""
    tasks = _load_json(TASKS_FILE)
    tasks = [t for t in tasks if t["id"] != task_id]
    _save_json(TASKS_FILE, tasks)
    return f"Tarea {task_id} eliminada."


# --- NOTAS ---
def add_note(title: str, content: str) -> dict:
    """Añade una nueva nota."""
    notes = _load_json(NOTES_FILE)
    note = {
        "id": len(notes) + 1,
        "titulo": title,
        "contenido": content,
        "creada": datetime.now().isoformat(),
    }
    notes.append(note)
    _save_json(NOTES_FILE, notes)
    return note


def list_notes() -> list:
    """Lista todas las notas."""
    return _load_json(NOTES_FILE)


def search_notes(query: str) -> list:
    """Busca notas por palabra clave."""
    notes = _load_json(NOTES_FILE)
    query_lower = query.lower()
    return [
        n for n in notes
        if query_lower in n["titulo"].lower() or query_lower in n["contenido"].lower()
    ]
