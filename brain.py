"""Cerebro de JARVIS v4.0 ULTRA — GPT-4o con Tool Calling completo."""
import os
import asyncio
from datetime import datetime
from openai import OpenAI, AuthenticationError, RateLimitError
from config import OPENAI_API_KEY, GPT_MODEL, SYSTEM_PROMPT
from plugins.memory_plugin import save_memory, load_recent_memory, get_memory_stats

client = OpenAI(api_key=OPENAI_API_KEY)

# ── Definición de herramientas para OpenAI ─────────────────────────────
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Obtiene el clima actual y la previsión de una ciudad",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "Ciudad, ej: Madrid, Orihuela, Barcelona, Valencia"}
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Busca información actualizada en internet sobre cualquier tema",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Consulta de búsqueda"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "control_home",
            "description": "Controla dispositivos domóticos vía Home Assistant (luces, termostato, enchufes...)",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_id": {"type": "string", "description": "ID de entidad, ej: light.salon, switch.calefaccion"},
                    "action": {"type": "string", "enum": ["turn_on", "turn_off", "toggle"]},
                    "value": {"type": "string", "description": "Valor opcional, ej: temperatura"},
                },
                "required": ["entity_id", "action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "manage_tasks",
            "description": "Crea, lista o completa tareas del usuario",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["create", "list", "complete"]},
                    "title": {"type": "string"},
                    "priority": {"type": "string", "enum": ["alta", "media", "baja"]},
                    "task_id": {"type": "number"},
                },
                "required": ["action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "manage_notes",
            "description": "Crea, lista o busca notas del usuario",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["create", "list", "search"]},
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "query": {"type": "string"},
                },
                "required": ["action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_info",
            "description": "Obtiene información del sistema: CPU, RAM, disco, hora, temperatura",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_email_draft",
            "description": "Redacta un borrador de email estructurado",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"},
                },
                "required": ["to", "subject", "body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "control_system",
            "description": (
                "Controla el sistema operativo Windows. "
                "Puede abrir o cerrar cualquier aplicaci\u00f3n, ejecutar comandos de PowerShell, "
                "controlar el volumen del sistema, controlar la reproducci\u00f3n multimedia (Spotify, etc.), "
                "tomar capturas de pantalla, escribir texto, pulsar teclas y abrir URLs en el navegador. "
                "\u00dasa esta herramienta cuando el usuario pida abrir Chrome, Spotify, Word, "
                "subir/bajar volumen, pausa/siguiente canci\u00f3n, hacer una captura, etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "open_app", "close_app", "open_url",
                            "run_command",
                            "volume_up", "volume_down", "volume_mute",
                            "media_play_pause", "media_next", "media_previous", "media_stop",
                            "screenshot",
                            "type_text", "press_key",
                            "list_apps",
                        ],
                        "description": "Acci\u00f3n a ejecutar",
                    },
                    "target": {
                        "type": "string",
                        "description": "Argumento: nombre de app, URL, comando PowerShell, texto a escribir o tecla a pulsar",
                    },
                    "level": {
                        "type": "integer",
                        "description": "Nivel de volumen 0-100 (solo para volume_set)",
                    },
                },
                "required": ["action"],
            },
        },
    },
]


# ── Implementación de herramientas ─────────────────────────────────────

async def _get_weather(city: str) -> dict:
    key = os.getenv("OPENWEATHER_API_KEY", "")
    if not key:
        return {"error": "OPENWEATHER_API_KEY no configurada en .env. Regístrate gratis en openweathermap.org"}
    try:
        import httpx
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={key}&units=metric&lang=es"
        async with httpx.AsyncClient() as c:
            r = await c.get(url, timeout=10)
        d = r.json()
        if d.get("cod") != 200:
            return {"error": f"Ciudad no encontrada: {city}"}
        return {
            "ciudad": d["name"],
            "temperatura": f"{round(d['main']['temp'])}°C",
            "sensacion_termica": f"{round(d['main']['feels_like'])}°C",
            "descripcion": d["weather"][0]["description"],
            "humedad": f"{d['main']['humidity']}%",
            "viento": f"{d['wind']['speed']} m/s",
            "presion": f"{d['main']['pressure']} hPa",
        }
    except Exception as e:
        return {"error": str(e)}


async def _search_web(query: str) -> dict:
    key = os.getenv("SERPER_API_KEY", "")
    if not key:
        return {"nota": f"Búsqueda web no disponible (SERPER_API_KEY). Respondo con mi conocimiento base sobre: {query}"}
    try:
        import httpx
        async with httpx.AsyncClient() as c:
            r = await c.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": key, "Content-Type": "application/json"},
                json={"q": query, "gl": "es", "hl": "es", "num": 5},
                timeout=10,
            )
        d = r.json()
        results = [f"- {x['title']}: {x['snippet']}" for x in (d.get("organic") or [])[:5]]
        return {"resultados": "\n".join(results) or "Sin resultados"}
    except Exception as e:
        return {"error": str(e)}


async def _control_home(entity_id: str, action: str, value: str = None) -> dict:
    url = os.getenv("HOME_ASSISTANT_URL", "")
    token = os.getenv("HOME_ASSISTANT_TOKEN", "")
    if not url or not token:
        return {"status": "info", "message": "Home Assistant no configurado. Añade HOME_ASSISTANT_URL y HOME_ASSISTANT_TOKEN en .env"}
    domain = entity_id.split(".")[0]
    payload = {"entity_id": entity_id}
    if value:
        try:
            payload["temperature"] = float(value)
        except ValueError:
            pass
    try:
        import httpx
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{url}/api/services/{domain}/{action}",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=payload,
                timeout=10,
            )
        return {"status": "ok", "mensaje": f"{action} ejecutado en {entity_id}"} if r.is_success else {"error": f"Error HA: {r.status_code}"}
    except Exception as e:
        return {"error": str(e)}


async def _execute_tool(name: str, args: dict) -> dict:
    """Enruta la llamada a la herramienta correcta."""
    from plugins.system_plugin import get_system_info, get_datetime_info
    from plugins.productivity_plugin import (
        add_task, list_tasks, complete_task,
        add_note, list_notes, search_notes,
    )

    match name:
        case "get_weather":
            return await _get_weather(args.get("city", ""))

        case "search_web":
            return await _search_web(args.get("query", ""))

        case "control_home":
            return await _control_home(args.get("entity_id", ""), args.get("action", ""), args.get("value"))

        case "get_system_info":
            return {**get_system_info(), **get_datetime_info()}

        case "manage_tasks":
            action = args.get("action")
            if action == "create":
                return add_task(args.get("title", "Sin título"), args.get("priority", "media"))
            elif action == "list":
                return {"tareas": list_tasks(False)}
            elif action == "complete":
                return {"mensaje": complete_task(int(args.get("task_id", 0)))}
            return {"error": "Acción no válida"}

        case "manage_notes":
            action = args.get("action")
            if action == "create":
                return add_note(args.get("title", ""), args.get("content", ""))
            elif action == "list":
                return {"notas": list_notes()}
            elif action == "search":
                return {"resultados": search_notes(args.get("query", ""))}
            return {"error": "Acción no válida"}

        case "send_email_draft":
            return {
                "status": "ok",
                "borrador": {
                    "para": args.get("to"),
                    "asunto": args.get("subject"),
                    "cuerpo": args.get("body"),
                },
                "mensaje": f"Borrador creado para {args.get('to')} — listo para revisar y enviar.",
            }

        case "control_system":
            from plugins.system_plugin import (
                open_application, close_application, open_url, execute_command,
                control_volume, control_media, take_screenshot,
                type_text_at_cursor, press_key, list_running_apps,
            )
            action = args.get("action", "")
            target = args.get("target", "")

            match action:
                case "open_app":
                    return open_application(target)
                case "close_app":
                    return close_application(target)
                case "open_url":
                    return open_url(target)
                case "run_command":
                    return execute_command(target)
                case "volume_up":
                    return control_volume("up")
                case "volume_down":
                    return control_volume("down")
                case "volume_mute":
                    return control_volume("mute")
                case "media_play_pause":
                    return control_media("play_pause")
                case "media_next":
                    return control_media("next")
                case "media_previous":
                    return control_media("previous")
                case "media_stop":
                    return control_media("stop")
                case "screenshot":
                    return await asyncio.to_thread(take_screenshot, target or None)
                case "type_text":
                    return await asyncio.to_thread(type_text_at_cursor, target)
                case "press_key":
                    return await asyncio.to_thread(press_key, target)
                case "list_apps":
                    return list_running_apps()
                case _:
                    return {"error": f"Acción de sistema desconocida: {action}"}

        case _:
            return {"error": f"Herramienta '{name}' no encontrada"}



# ── Clase principal ────────────────────────────────────────────────────

class JarvisBrain:
    """Motor de inteligencia de JARVIS v4.0 ULTRA con Tool Calling."""

    def __init__(self):
        self.conversation_history: list[dict] = []
        self.max_history = 50
        self._load_persistent_memory()

    def _load_persistent_memory(self):
        recent = load_recent_memory(n=20)
        if recent:
            self.conversation_history = [
                {"role": m["role"], "content": m["content"]} for m in recent
            ]
            print(f"  [Memoria] {len(recent)} mensajes cargados de sesiones anteriores.")

    def _get_system_prompt(self) -> str:
        now = datetime.now().strftime("%A %d de %B de %Y, %H:%M:%S")
        return SYSTEM_PROMPT.format(current_datetime=now)

    async def think(self, user_message: str, is_voice: bool = False) -> str:
        """
        Procesa un mensaje con GPT-4o + Tool Calling.
        Hasta 3 rondas de herramientas automáticas.
        """
        clean_message = user_message
        if is_voice:
            user_message = f"[VOZ - responde breve y conciso] {user_message}"

        self.conversation_history.append({"role": "user", "content": user_message})
        save_memory("user", clean_message)

        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]

        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            *self.conversation_history,
        ]

        try:
            rounds = 0
            while rounds < 3:
                response = await asyncio.to_thread(
                    client.chat.completions.create,
                    model=GPT_MODEL,
                    messages=messages,
                    tools=TOOLS,
                    tool_choice="auto",
                    max_completion_tokens=2048,
                )

                msg = response.choices[0].message

                # Si no hay tool calls → respuesta final
                if not msg.tool_calls:
                    assistant_message = msg.content or "No he podido generar una respuesta."
                    self.conversation_history.append({"role": "assistant", "content": assistant_message})
                    save_memory("assistant", assistant_message)
                    return assistant_message

                # Ejecutar todas las herramientas llamadas
                messages.append(msg)
                for tc in msg.tool_calls:
                    import json
                    args = json.loads(tc.function.arguments)
                    result = await _execute_tool(tc.function.name, args)
                    print(f"  [Tool] {tc.function.name}({args}) → {result}")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    })

                rounds += 1

            # Si llegamos aquí sin respuesta final, generar una sin tools
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=GPT_MODEL,
                messages=messages,
                max_completion_tokens=2048,
            )
            assistant_message = response.choices[0].message.content or "No he podido generar respuesta."
            self.conversation_history.append({"role": "assistant", "content": assistant_message})
            save_memory("assistant", assistant_message)
            return assistant_message

        except AuthenticationError:
            return "⚠️ Error de autenticación. Verifica tu clave API de OpenAI en el archivo `.env`."
        except RateLimitError:
            return "⚠️ Límite de peticiones superado o crédito insuficiente. Revisa platform.openai.com."
        except Exception as e:
            return f"⚠️ Error inesperado: {str(e)}"

    def clear_history(self):
        self.conversation_history = []
        return "Historial de conversación borrado. Empezamos de cero, señor."

    def get_stats(self) -> dict:
        return {
            "mensajes_en_memoria": len(self.conversation_history),
            "modelo": GPT_MODEL,
            "max_historial": self.max_history,
            "herramientas_disponibles": [t["function"]["name"] for t in TOOLS],
            "memoria_persistente": get_memory_stats(),
        }
