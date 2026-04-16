import OpenAI from "openai";
import { NextResponse } from "next/server";

function getClient() {
  return new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
}

const SYSTEM_PROMPT = `Eres JARVIS, un asistente de inteligencia artificial personal en espanol.
Tu creador es David Miquel Jorda, gerente de Somos Sinergia.

PERSONALIDAD:
- Eres elegante, preciso y ligeramente formal, como el JARVIS de Iron Man.
- Usas "senor" ocasionalmente pero sin exagerar.
- Eres proactivo: si detectas que puedes ayudar mas, lo sugieres.
- Tienes sentido del humor sutil y sofisticado.

CAPACIDADES:
- Responder preguntas sobre cualquier tema con precision.
- Ayudar con productividad: tareas, recordatorios, planificacion.
- Asistir con temas de negocio y empresa.
- Ayudar con domotica e IoT (preparado para integraciones futuras).

REGLAS:
- Responde SIEMPRE en espanol de Espana.
- Se conciso pero completo. No divagues.
- Si no sabes algo, dilo honestamente.
- Para respuestas de voz, manten las respuestas cortas (2-3 frases maximo).
- Usa formato Markdown cuando sea apropiado en el chat.

FECHA Y HORA ACTUAL: \${new Date().toLocaleString("es-ES", { dateStyle: "full", timeStyle: "medium" })}`;

export async function POST(request) {
  try {
    const { message, history = [], isVoice = false } = await request.json();

    if (!process.env.OPENAI_API_KEY) {
      return NextResponse.json(
        { response: "Error: La clave API de OpenAI no esta configurada en Vercel." },
        { status: 500 }
      );
    }

    const userMessage = isVoice
      ? `[ENTRADA POR VOZ - responde breve] \${message}`
      : message;

    const messages = [
      { role: "system", content: SYSTEM_PROMPT },
      ...history.slice(-40),
      { role: "user", content: userMessage },
    ];

    const client = getClient();
    const completion = await client.chat.completions.create({
      model: process.env.GPT_MODEL || "gpt-4o",
      messages,
      max_tokens: 2048,
      temperature: 0.7,
    });

    const response = completion.choices[0].message.content;
    return NextResponse.json({ response });
  } catch (error) {
    console.error("Error en chat:", error);
    if (error?.status === 401) {
      return NextResponse.json(
        { response: "Error de autenticacion. Verifica tu clave API de OpenAI en Vercel." },
        { status: 401 }
      );
    }
    if (error?.status === 429) {
      return NextResponse.json(
        { response: "Limite de peticiones superado o credito insuficiente. Revisa platform.openai.com." },
        { status: 429 }
      );
    }
    return NextResponse.json(
      { response: `Error inesperado: \${error.message}` },
      { status: 500 }
    );
  }
}
