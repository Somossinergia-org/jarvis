import { NextResponse } from "next/server";

export async function POST() {
  return NextResponse.json({
    message: "Historial de conversacion borrado. Empezamos de cero, senor.",
  });
}
