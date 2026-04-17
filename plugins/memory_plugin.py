"""Plugin de memoria persistente para Jarvis."""
import json
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

MEMORY_FILE = os.path.join(DATA_DIR, "memory.json")
MAX_MEMORY_ENTRIES = 100  # Máximo de entradas a conservar


def _load_memory() -> list:
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_memory(entries: list):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def save_memory(role: str, content: str):
    """Guarda un mensaje en la memoria persistente."""
    entries = _load_memory()
    entries.append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat(),
    })
    # Mantener solo los últimos MAX_MEMORY_ENTRIES
    if len(entries) > MAX_MEMORY_ENTRIES:
        entries = entries[-MAX_MEMORY_ENTRIES:]
    _save_memory(entries)


def load_recent_memory(n: int = 20) -> list:
    """Carga los últimos N mensajes de la memoria persistente."""
    entries = _load_memory()
    return entries[-n:] if len(entries) > n else entries


def get_memory_stats() -> dict:
    """Estadísticas de la memoria persistente."""
    entries = _load_memory()
    return {
        "total_entradas": len(entries),
        "primera_entrada": entries[0]["timestamp"] if entries else None,
        "ultima_entrada": entries[-1]["timestamp"] if entries else None,
        "archivo": MEMORY_FILE,
    }


def clear_memory():
    """Borra toda la memoria persistente."""
    _save_memory([])
    return "Memoria borrada. Empezamos desde cero, señor."
