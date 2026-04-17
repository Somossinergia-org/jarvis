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

CAPACIDADES - Usa las herramientas (tools) disponibles cuando sea necesario:
- get_weather: Consultar el clima de cualquier ciudad.
- control_home: Controlar dispositivos de domotica via Home Assistant.
- search_web: Buscar informacion actualizada en internet.
- manage_notes: Crear, listar y buscar notas.
- manage_tasks: Crear, listar y completar tareas.
- get_system_time: Obtener la fecha y hora actual.
- send_email_draft: Crear borradores de email.

REGLAS:
- Responde SIEMPRE en espanol de Espana.
- Se conciso pero completo.
- Usa las herramientas cuando el usuario pida algo que requiera datos externos o acciones.
- Usa formato Markdown cuando sea apropiado.
- Para respuestas de voz, se breve (2-3 frases).`;

const tools = [
  { type: "function", function: { name: "get_weather", description: "Obtiene el clima actual de una ciudad", parameters: { type: "object", properties: { city: { type: "string", description: "Ciudad, ej: Madrid, Orihuela" } }, required: ["city"] } } },
  { type: "function", function: { name: "control_home", description: "Controla dispositivos de domotica via Home Assistant", parameters: { type: "object", properties: { entity_id: { type: "string", description: "ID entidad, ej: light.salon" }, action: { type: "string", enum: ["turn_on","turn_off","toggle","set_temperature"] }, value: { type: "string", description: "Valor opcional" } }, required: ["entity_id","action"] } } },
  { type: "function", function: { name: "search_web", description: "Busca informacion en internet", parameters: { type: "object", properties: { query: { type: "string" } }, required: ["query"] } } },
  { type: "function", function: { name: "manage_notes", description: "Gestiona notas: crear, listar, buscar", parameters: { type: "object", properties: { action: { type: "string", enum: ["create","list","search"] }, title: { type: "string" }, content: { type: "string" }, query: { type: "string" } }, required: ["action"] } } },
  { type: "function", function: { name: "manage_tasks", description: "Gestiona tareas: crear, listar, completar", parameters: { type: "object", properties: { action: { type: "string", enum: ["create","list","complete"] }, title: { type: "string" }, priority: { type: "string", enum: ["alta","media","baja"] }, task_id: { type: "number" } }, required: ["action"] } } },
  { type: "function", function: { name: "get_system_time", description: "Fecha y hora actual", parameters: { type: "object", properties: {} } } },
  { type: "function", function: { name: "send_email_draft", description: "Crea borrador de email", parameters: { type: "object", properties: { to: { type: "string" }, subject: { type: "string" }, body: { type: "string" } }, required: ["to","subject","body"] } } }
];

async function executeTool(name, args) {
  switch(name) {
    case "get_weather": return await getWeather(args.city);
    case "control_home": return await controlHome(args.entity_id, args.action, args.value);
    case "search_web": return await searchWeb(args.query);
    case "manage_notes": return manageNotes(args);
    case "manage_tasks": return manageTasks(args);
    case "get_system_time": return { datetime: new Date().toLocaleString("es-ES", { dateStyle: "full", timeStyle: "medium", timeZone: "Europe/Madrid" }) };
    case "send_email_draft": return { status: "ok", message: "Borrador creado para " + args.to + ": " + args.subject };
    default: return { error: "Herramienta no encontrada" };
  }
}

async function getWeather(city) {
  const k = process.env.OPENWEATHER_API_KEY;
  if (!k) return { error: "OPENWEATHER_API_KEY no configurada en Vercel." };
  try {
    const r = await fetch("https://api.openweathermap.org/data/2.5/weather?q=" + encodeURIComponent(city) + "&appid=" + k + "&units=metric&lang=es");
    const d = await r.json();
    if (d.cod !== 200) return { error: "Ciudad no encontrada: " + city };
    return { ciudad: d.name, temperatura: Math.round(d.main.temp) + "C", sensacion: Math.round(d.main.feels_like) + "C", descripcion: d.weather[0].description, humedad: d.main.humidity + "%", viento: d.wind.speed + " m/s" };
  } catch (e) { return { error: e.message }; }
}

async function controlHome(entityId, action, value) {
  const u = process.env.HOME_ASSISTANT_URL, t = process.env.HOME_ASSISTANT_TOKEN;
  if (!u || !t) return { status: "info", message: "Home Assistant no configurado. Anade HOME_ASSISTANT_URL y HOME_ASSISTANT_TOKEN en Vercel." };
  const domain = entityId.split(".")[0];
  const payload = { entity_id: entityId };
  if (action === "set_temperature" && value) payload.temperature = parseFloat(value);
  try {
    const r = await fetch(u + "/api/services/" + domain + "/" + action, { method: "POST", headers: { "Authorization": "Bearer " + t, "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    return r.ok ? { status: "ok", message: action + " ejecutado en " + entityId } : { error: "Error HA: " + r.status };
  } catch (e) { return { error: e.message }; }
}

async function searchWeb(query) {
  const k = process.env.SERPER_API_KEY;
  if (!k) return { result: "Busqueda web no disponible. Registrate gratis en serper.dev y anade SERPER_API_KEY. Respondo con mi conocimiento sobre: " + query };
  try {
    const r = await fetch("https://google.serper.dev/search", { method: "POST", headers: { "X-API-KEY": k, "Content-Type": "application/json" }, body: JSON.stringify({ q: query, gl: "es", hl: "es", num: 5 }) });
    const d = await r.json();
    return { results: (d.organic || []).slice(0,4).map(x => "- " + x.title + ": " + x.snippet).join("\n") || "Sin resultados" };
  } catch (e) { return { error: e.message }; }
}

const notes = [];
function manageNotes(a) {
  if (a.action === "create") { const n = { id: notes.length+1, title: a.title||"Sin titulo", content: a.content||"", created: new Date().toLocaleString("es-ES") }; notes.push(n); return { status: "ok", note: n }; }
  if (a.action === "list") return { notes: notes.length ? notes : "No hay notas." };
  if (a.action === "search") { const q = (a.query||"").toLowerCase(); return { results: notes.filter(n => n.title.toLowerCase().includes(q) || n.content.toLowerCase().includes(q)) }; }
  return { error: "Accion no valida" };
}

const tasks = [];
function manageTasks(a) {
  if (a.action === "create") { const t = { id: tasks.length+1, title: a.title||"Sin titulo", priority: a.priority||"media", done: false, created: new Date().toLocaleString("es-ES") }; tasks.push(t); return { status: "ok", task: t }; }
  if (a.action === "list") { const p = tasks.filter(t => !t.done); return { tasks: p.length ? p : "No hay tareas pendientes." }; }
  if (a.action === "complete") { const t = tasks.find(x => x.id === a.task_id); if (t) { t.done = true; return { status: "ok", message: "Tarea completada: " + t.title }; } return { error: "Tarea no encontrada." }; }
  return { error: "Accion no valida" };
}

export async function POST(request) {
  try {
    const { message, history = [], isVoice = false } = await request.json();
    if (!process.env.OPENAI_API_KEY) return NextResponse.json({ response: "Error: OPENAI_API_KEY no configurada." }, { status: 500 });
    const userMessage = isVoice ? "[VOZ - breve] " + message : message;
    const messages = [{ role: "system", content: SYSTEM_PROMPT }, ...history.slice(-30), { role: "user", content: userMessage }];
    const client = getClient();
    let c = await client.chat.completions.create({ model: process.env.GPT_MODEL || "gpt-4o", messages, tools, tool_choice: "auto", max_tokens: 2048, temperature: 0.7 });
    let msg = c.choices[0].message;
    let rounds = 0;
    while (msg.tool_calls && msg.tool_calls.length > 0 && rounds < 3) {
      messages.push(msg);
      for (const tc of msg.tool_calls) {
        const args = JSON.parse(tc.function.arguments);
        const result = await executeTool(tc.function.name, args);
        messages.push({ role: "tool", tool_call_id: tc.id, content: JSON.stringify(result) });
      }
      c = await client.chat.completions.create({ model: process.env.GPT_MODEL || "gpt-4o", messages, tools, max_tokens: 2048, temperature: 0.7 });
      msg = c.choices[0].message;
      rounds++;
    }
    return NextResponse.json({ response: msg.content || "No he podido generar respuesta." });
  } catch (error) {
    if (error?.status === 401) return NextResponse.json({ response: "Error autenticacion. Verifica OPENAI_API_KEY." }, { status: 401 });
    if (error?.status === 429) return NextResponse.json({ response: "Sin credito. Revisa platform.openai.com." }, { status: 429 });
    return NextResponse.json({ response: "Error: " + error.message }, { status: 500 });
  }
                              }
