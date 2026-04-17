"""
Motor TTS de JARVIS v4.0 ULTRA
Prioridad: ElevenLabs (voz JARVIS real) → OpenAI tts-1-hd (onyx) → Edge-TTS (gratis)
"""
import os
import hashlib
import asyncio
import re
import edge_tts
from config import TTS_VOICE, AUDIO_CACHE_DIR, OPENAI_API_KEY

os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")  # George — British, autoritario
OPENAI_TTS_VOICE   = os.getenv("OPENAI_TTS_VOICE", "onyx")

_OPENAI_VOICES = {"onyx", "alloy", "echo", "fable", "shimmer", "nova"}

# Configuración óptima para sonido tipo JARVIS
ELEVEN_SETTINGS = {
    "stability":        0.55,   # consistente pero natural
    "similarity_boost": 0.80,   # fiel a la voz original
    "style":            0.40,   # algo de expresividad
    "use_speaker_boost": True,  # claridad máxima
}


def _clean_text(text: str) -> str:
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"[*#_`~>\[\]()!]", "", text)
    text = re.sub(r"\n+", ". ", text)
    return text.strip()[:4096]


async def _elevenlabs_tts(text: str, voice_id: str, api_key: str, audio_path: str) -> bool:
    """Genera audio con ElevenLabs. Devuelve True si tuvo éxito."""
    try:
        import httpx
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key,
        }
        payload = {
            "text": text[:5000],
            "model_id": "eleven_multilingual_v2",  # soporta español perfectamente
            "voice_settings": ELEVEN_SETTINGS,
        }
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(url, headers=headers, json=payload)
        if r.status_code == 200:
            with open(audio_path, "wb") as f:
                f.write(r.content)
            return True
        else:
            print(f"  [TTS ElevenLabs] Error {r.status_code}: {r.text[:200]}")
            return False
    except Exception as e:
        print(f"  [TTS ElevenLabs] Excepción: {e}")
        return False


async def _openai_tts(text: str, voice: str, audio_path: str) -> bool:
    """Genera audio con OpenAI TTS. Devuelve True si tuvo éxito."""
    if not OPENAI_API_KEY:
        return False
    for model in ["tts-1-hd", "tts-1"]:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            response = await asyncio.to_thread(
                client.audio.speech.create,
                model=model,
                voice=voice,
                input=text,
                speed=1.05,
                response_format="mp3",
            )
            audio_data = await asyncio.to_thread(response.read)
            with open(audio_path, "wb") as f:
                f.write(audio_data)
            return True
        except Exception as e:
            print(f"  [TTS OpenAI {model}] Error: {e}")
    return False



async def _edgetts_tts(text: str, voice: str, audio_path: str) -> bool:
    """Genera audio con Edge-TTS (Microsoft, gratis). Fallback final."""
    try:
        communicate = edge_tts.Communicate(text[:3000], voice)
        await communicate.save(audio_path)
        return True
    except Exception as e:
        print(f"  [TTS Edge-TTS] Error: {e}")
        return False


async def text_to_speech(text: str, voice: str | None = None) -> str:
    """
    Convierte texto a MP3 con la mejor voz disponible.
    Prioridad: ElevenLabs (JARVIS real) → OpenAI Onyx → Edge-TTS
    """
    clean = _clean_text(text)
    if not clean:
        raise ValueError("Texto vacío para TTS")

    # ElevenLabs siempre usa su propio voice_id (no el parámetro voice de OpenAI)
    el_voice = ELEVENLABS_VOICE_ID  # George, Callum, etc.
    cache_key = hashlib.md5(f"{clean}:{el_voice if ELEVENLABS_API_KEY else 'no_el'}".encode()).hexdigest()
    audio_path = os.path.join(AUDIO_CACHE_DIR, f"{cache_key}.mp3")

    if os.path.exists(audio_path):
        return audio_path

    # ── 1. ElevenLabs (voz JARVIS más cercana) ─────────────────
    if ELEVENLABS_API_KEY:
        ok = await _elevenlabs_tts(clean, el_voice, ELEVENLABS_API_KEY, audio_path)
        if ok:
            print(f"  [TTS] ✅ ElevenLabs George (voz JARVIS)")
            return audio_path
        print("  [TTS] ⚠️  ElevenLabs falló → probando OpenAI...")

    # ── 2. OpenAI tts-1-hd "onyx" ───────────────────────────
    openai_voice = OPENAI_TTS_VOICE  # siempre onyx para OpenAI
    ok = await _openai_tts(clean, openai_voice, audio_path)
    if ok:
        print(f"  [TTS] ✅ OpenAI ({openai_voice})")
        return audio_path
    print("  [TTS] ⚠️  OpenAI falló → usando Edge-TTS...")

    # ── 3. Edge-TTS (Microsoft, siempre disponible) ─────────────
    ok = await _edgetts_tts(clean, TTS_VOICE, audio_path)
    if ok:
        print(f"  [TTS] ✅ Edge-TTS ({TTS_VOICE})")
        return audio_path

    raise RuntimeError("Todos los motores TTS fallaron")



async def list_spanish_voices() -> list[dict]:
    """Lista voces en español de Edge-TTS."""
    voices = await edge_tts.list_voices()
    return [
        {"name": v["ShortName"], "gender": v["Gender"], "locale": v["Locale"]}
        for v in voices if v["Locale"].startswith("es-")
    ]


def clean_cache(max_files: int = 500):
    """Limpia la caché de audio si supera el límite."""
    try:
        files = [
            (os.path.join(AUDIO_CACHE_DIR, f), os.path.getmtime(os.path.join(AUDIO_CACHE_DIR, f)))
            for f in os.listdir(AUDIO_CACHE_DIR)
            if os.path.isfile(os.path.join(AUDIO_CACHE_DIR, f))
        ]
        if len(files) > max_files:
            files.sort(key=lambda x: x[1])
            for filepath, _ in files[:len(files) - max_files]:
                os.remove(filepath)
    except Exception:
        pass
