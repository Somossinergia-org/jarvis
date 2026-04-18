import OpenAI from "openai";

let client = null;
function getClient() {
  if (!client) client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
  return client;
}

export async function POST(request) {
  try {
    const { text, voice = "onyx" } = await request.json();
    if (!text || !text.trim()) {
      return Response.json({ error: "No text provided" }, { status: 400 });
    }

    const openai = getClient();
    const cleanText = text
      .replace(/[*#_\`~>\[\]()!]/g, "")
      .replace(/\n+/g, ". ")
      .substring(0, 4096);

    const mp3 = await openai.audio.speech.create({
      model: "tts-1-hd",
      voice: voice,
      input: cleanText,
      speed: 1.05,
      response_format: "mp3",
    });

    const buffer = Buffer.from(await mp3.arrayBuffer());
    return new Response(buffer, {
      headers: {
        "Content-Type": "audio/mpeg",
        "Cache-Control": "no-cache",
      },
    });
  } catch (error) {
    console.error("TTS Error:", error.message);
    return Response.json(
      { error: "Voice synthesis failed", details: error.message },
      { status: 500 }
    );
  }
}
