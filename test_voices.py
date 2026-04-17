"""Test de voces disponibles para JARVIS en español."""
import asyncio, os, sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
import httpx, edge_tts

ELEVEN_KEY = os.getenv("ELEVENLABS_API_KEY", "")
TEST_TEXT  = "Sistema en línea. Bienvenido, señor. Estoy listo para asistirle."

# Voces ElevenLabs con acento español/latino conocidas
SPANISH_VOICES = {
    "Valentino (Latino)":    "pqHfZKP75CvOlQylNhV4",   # Bill/deep
    "Mateo (Español)":       "oWAxZDx7w5VEj9dCyTzz",
    "Lorenzo (Español)":     "IKne3meq5aSn9XLyUdCD",
    "Sergi (Español)":       "pMsXgVXv3BLzUgSXRplE",
    "Daniel (British+ES)":   "onwK4e9ZLuTAKqWW03F9",
    "Liam (Multilingual)":   "TX3LPaxmHKxFdv7VOQHJ",
}

async def test_eleven(name, vid):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{vid}"
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(url,
            headers={"Accept": "audio/mpeg", "Content-Type": "application/json", "xi-api-key": ELEVEN_KEY},
            json={"text": TEST_TEXT, "model_id": "eleven_multilingual_v2",
                  "voice_settings": {"stability": 0.55, "similarity_boost": 0.80}})
    if r.status_code == 200:
        path = f"test_{vid[:8]}.mp3"
        with open(path, "wb") as f: f.write(r.content)
        print(f"  OK {name} | ID:{vid[:12]} | {len(r.content)} bytes -> {path}")
        return True
    else:
        print(f"  FAIL {name} | {r.status_code}: {r.json().get('detail',{}).get('message','err')[:60]}")
        return False

async def test_edge():
    try:
        c = edge_tts.Communicate(TEST_TEXT, "es-ES-AlvaroNeural")
        await c.save("test_edge_es.mp3")
        print(f"  OK Edge-TTS es-ES-AlvaroNeural -> test_edge_es.mp3")
        return True
    except Exception as e:
        print(f"  FAIL Edge-TTS: {e}")
        return False

async def main():
    print("\n=== Probando voces ElevenLabs en español ===")
    for name, vid in SPANISH_VOICES.items():
        await test_eleven(name, vid)

    print("\n=== Probando Edge-TTS (Microsoft) ===")
    await test_edge()

asyncio.run(main())
