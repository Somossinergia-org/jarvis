"""Motor TTS: OpenAI tts-1-hd como principal, Edge-TTS como fallback."""
import os
import hashlib
import asyncio
import re
import edge_tts
from config import TTS_VOICE, AUDIO_CACHE_DIR, OPENAI_API_KEY

os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)

_OPENAI_VOICES = {"onyx", "alloy", "echo", "fable", "shimmer", "nova"}


def _clean_text(text: str) -> str:
    """Limpia markdown y caracteres especiales para TTS."""
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"[*#_`~>\[\]()!]", "", text)
    text = re.sub(r"\n+", ". ", text)
    return text.strip()[:4096]


async def text_to_speech(text: str, voice: str | None = None) -> str:
    """
    Convierte texto a audio MP3.
    1. Intenta OpenAI tts-1-hd (voz "onyx" por defecto — la más natural)
    2. Fallback a Edge-TTS (gratis, Microsoft) si OpenAI falla
    """
    clean = _clean_text(text)
    if not clean:
        raise ValueError("Texto vacío para TTS")

    openai_voice = voice or os.getenv("OPENAI_TTS_VOICE", "onyx")
    if openai_voice not in _OPENAI_VOICES:
        openai_voice = "onyx"

    cache_key = hashlib.md5(f"{clean}:{openai_voice}".encode()).hexdigest()
    audio_path = os.path.join(AUDIO_CACHE_DIR, f"{cache_key}.mp3")

    if os.path.exists(audio_path):
        return audio_path

    # ── 1. OpenAI TTS (tts-1-hd) ──────────────────────────────
    if OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            response = await asyncio.to_thread(
                client.audio.speech.create,
                model="tts-1-hd",
                voice=openai_voice,
                input=clean,
                speed=1.05,
                response_format="mp3",
            )
            audio_data = await asyncio.to_thread(response.read)
            with open(audio_path, "wb") as f:
                f.write(audio_data)
            return audio_path
        except Exception as e:
            print(f"  [TTS] OpenAI falló ({e}), usando Edge-TTS como fallback...")

    # ── 2. Edge-TTS (fallback gratuito) ───────────────────────
    edge_voice = TTS_VOICE
    communicate = edge_tts.Communicate(clean, edge_voice)
    await communicate.save(audio_path)
    return audio_path


async def list_spanish_voices() -> list[dict]:
    """Lista voces en español de Edge-TTS."""
    voices = await edge_tts.list_voices()
    return [
        {"name": v["ShortName"], "gender": v["Gender"], "locale": v["Locale"]}
        for v in voices if v["Locale"].startswith("es-")
    ]


def clean_cache(max_files: int = 500):
    """Limpia la caché de audio si supera el límite."""
    files = [
        (os.path.join(AUDIO_CACHE_DIR, f), os.path.getmtime(os.path.join(AUDIO_CACHE_DIR, f)))
        for f in os.listdir(AUDIO_CACHE_DIR)
        if os.path.isfile(os.path.join(AUDIO_CACHE_DIR, f))
    ]
    if len(files) > max_files:
        files.sort(key=lambda x: x[1])
        for filepath, _ in files[:len(files) - max_files]:
            os.remove(filepath)
