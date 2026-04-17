"""Cerebro de Jarvis: integración con la API de OpenAI (ChatGPT)."""
import asyncio
from openai import OpenAI, AuthenticationError, RateLimitError
from datetime import datetime
from config import OPENAI_API_KEY, GPT_MODEL, SYSTEM_PROMPT
from plugins.memory_plugin import save_memory, load_recent_memory, clear_memory as _clear_mem


client = OpenAI(api_key=OPENAI_API_KEY)


class JarvisBrain:
    """Gestiona la conversación y la inteligencia de Jarvis."""

    def __init__(self):
        self.conversation_history: list[dict] = []
        self.max_history = 50  # Máximo de mensajes en memoria RAM

        # Cargar memoria persistente al arrancar
        self._load_persistent_memory()

    def _load_persistent_memory(self):
        """Carga los últimos mensajes guardados en disco al iniciar."""
        recent = load_recent_memory(n=20)
        if recent:
            # Convertir al formato de OpenAI (solo role + content)
            self.conversation_history = [
                {"role": m["role"], "content": m["content"]}
                for m in recent
            ]
            print(f"  [Memoria] {len(recent)} mensajes cargados de sesiones anteriores.")

    def _get_system_prompt(self) -> str:
        """Genera el prompt del sistema con la fecha/hora actual."""
        now = datetime.now().strftime("%A %d de %B de %Y, %H:%M:%S")
        return SYSTEM_PROMPT.format(current_datetime=now)

    async def think(self, user_message: str, is_voice: bool = False) -> str:
        """
        Procesa un mensaje del usuario y devuelve la respuesta de Jarvis.

        Args:
            user_message: El mensaje del usuario.
            is_voice: Si viene de entrada de voz (respuestas más cortas).
        """
        # Añadir contexto de voz si aplica
        clean_message = user_message
        if is_voice:
            user_message = f"[ENTRADA POR VOZ - responde de forma breve y concisa] {user_message}"

        # Añadir mensaje del usuario al historial RAM
        self.conversation_history.append({
            "role": "user",
            "content": user_message,
        })

        # Guardar en memoria persistente (sin el prefijo de voz)
        save_memory("user", clean_message)

        # Recortar historial si es muy largo
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]

        # Construir mensajes para la API (system + historial)
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            *self.conversation_history,
        ]

        try:
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=GPT_MODEL,
                messages=messages,
                max_tokens=2048,
                temperature=0.7,
            )

            assistant_message = response.choices[0].message.content

            # Añadir respuesta al historial RAM
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message,
            })

            # Guardar en memoria persistente
            save_memory("assistant", assistant_message)

            return assistant_message

        except AuthenticationError:
            return ("⚠️ Error de autenticación. Verifica tu clave API de OpenAI "
                    "en el archivo `.env`.")
        except RateLimitError:
            return ("⚠️ Se ha superado el límite de peticiones o crédito insuficiente. "
                    "Revisa tu cuenta en platform.openai.com.")
        except Exception as e:
            return f"⚠️ Error inesperado: {str(e)}"

    def clear_history(self):
        """Limpia el historial de conversación en RAM (no borra la memoria persistente)."""
        self.conversation_history = []
        return "Historial de conversación borrado. Empezamos de cero, señor."

    def get_stats(self) -> dict:
        """Devuelve estadísticas de la sesión."""
        from plugins.memory_plugin import get_memory_stats
        return {
            "mensajes_en_memoria": len(self.conversation_history),
            "modelo": GPT_MODEL,
            "max_historial": self.max_history,
            "memoria_persistente": get_memory_stats(),
        }
