# 🤖 J.A.R.V.I.S. — Asistente Personal de IA en Español

Asistente personal inteligente con interfaz de chat y voz, potenciado por **OpenAI GPT-4o**.

---

## Requisitos

- **Python 3.10+** → [Descargar](https://www.python.org/downloads/)
- **Clave API de OpenAI** → [Obtener aquí](https://platform.openai.com/api-keys)
- **Navegador moderno** (Chrome/Edge recomendado para voz)

---

## Instalación rápida

```bash
# 1. Abre una terminal en la carpeta del proyecto

# 2. Instala las dependencias
pip install -r requirements.txt

# 3. Configura tu clave API
#    Copia .env.example a .env y edítalo
cp .env.example .env
#    Pon tu clave API de OpenAI en OPENAI_API_KEY

# 4. Arranca JARVIS
python start.py
```

Se abrirá automáticamente en **http://localhost:8000**.

---

## Funcionalidades

### Chat inteligente
Escribe cualquier pregunta o petición. JARVIS responde con la potencia de GPT-4o.

### Voz
- Pulsa el botón del micrófono (o `Ctrl+Shift+Espacio`) para hablar.
- JARVIS responde con voz en español (voces de Microsoft Edge-TTS, gratuitas).
- Activa/desactiva la respuesta por voz con el toggle de abajo.

### Plugins incluidos
- **Sistema**: info del PC, hora, estado del hardware.
- **Productividad**: tareas y notas (se guardan en `data/`).
- **Domótica**: preparado para integrar con Home Assistant u otros.

---

## Personalización

### Cambiar la voz
Edita `TTS_VOICE` en `.env`. Opciones en español:

| Voz | Código |
|-----|--------|
| Álvaro (España, masculina) | `es-ES-AlvaroNeural` |
| Elvira (España, femenina) | `es-ES-ElviraNeural` |
| Jorge (México, masculina) | `es-MX-JorgeNeural` |
| Dalia (México, femenina) | `es-MX-DaliaNeural` |

### Cambiar el modelo
Edita `GPT_MODEL` en `.env`. Opciones: `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, `gpt-3.5-turbo`.

### Cambiar la personalidad
Edita `SYSTEM_PROMPT` en `config.py` para ajustar el tono y comportamiento.

---

## Estructura del proyecto

```
jarvis/
├── server.py          # Servidor FastAPI principal
├── brain.py           # Integración con OpenAI API
├── config.py          # Configuración central
├── tts_engine.py      # Motor de voz (Edge-TTS)
├── start.py           # Script de arranque
├── requirements.txt   # Dependencias Python
├── .env.example       # Plantilla de configuración
├── static/
│   └── index.html     # Interfaz web completa
├── plugins/
│   ├── system_plugin.py       # Info del sistema
│   └── productivity_plugin.py # Tareas y notas
├── audio_cache/       # Caché de audio generado
└── data/              # Datos persistentes (tareas, notas)
```

---

## Atajos de teclado

| Atajo | Acción |
|-------|--------|
| `Enter` | Enviar mensaje |
| `Shift+Enter` | Nueva línea |
| `Ctrl+Shift+Espacio` | Activar micrófono |

---

## Creado para Somos Sinergia
por David Miquel Jordá
