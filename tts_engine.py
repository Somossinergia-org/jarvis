"""Motor de Text-to-Speech usando Edge-TTS (voces de Microsoft, gratis)."""
import os
import hashlib
import asyncio
import edge_tts
from config import TTS_VOICE, AUDIO_CACHE_DIR


os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)


async def text_to_speech(text: str, voice: str | None = None) -> str:
    """
    Convierte texto a audio MP3 usando Edge-TTS.
    Devuelve la ruta al archivo de audio generado.
    Usa caché para no regenerar el mismo texto.
    """
    voice = voice or TTS_VOICE

    # Crear hash para caché
    cache_key = hashlib.md5(f"{text}:{voice}".encode()).hexdigest()
    audio_path = os.path.join(AUDIO_CACHE_DIR, f"{cache_key}.mp3")

    # Si ya existe en caché, devolver directamente
    if os.path.exists(audio_path):
        return audio_path

    # Generar audio
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(audio_path)

    return audio_path


async def list_spanish_voices() -> list[dict]:
    """Lista todas las voces disponibles en español."""
    voices = await edge_tts.list_voices()
    spanish_voices = [
        {
            "name": v["ShortName"],
            "gender": v["Gender"],
            "locale": v["Locale"],
        }
        for v in voices
        if v["Locale"].startswith("es-")
    ]
    return spanish_voices


def clean_cache(max_files: int = 500):
    """Limpia la caché de audio si supera el máximo de archivos."""
    files = []
    for f in os.listdir(AUDIO_CACHE_DIR):
        filepath = os.path.join(AUDIO_CACHE_DIR, f)
        if os.path.isfile(filepath):
            files.append((filepath, os.path.getmtime(filepath)))

    if len(files) > max_files:
        # Borrar los más antiguos
        files.sort(key=lambda x: x[1])
        for filepath, _ in files[:len(files) - max_files]:
            os.remove(filepath)
