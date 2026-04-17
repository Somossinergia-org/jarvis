#!/usr/bin/env python3
"""
🤖 J.A.R.V.I.S. — Arrancador del sistema
Ejecuta: python start.py
"""
import subprocess
import sys
import os


def check_dependencies():
    """Verifica e instala dependencias."""
    print("🔍 Verificando dependencias...")
    try:
        import fastapi
        import openai
        import edge_tts
        import uvicorn
        import psutil
        print("   ✅ Todas las dependencias instaladas.")
    except ImportError as e:
        print(f"   ⚠️ Falta: {e.name}")
        print("   📦 Instalando dependencias...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt",
            "--quiet"
        ])
        print("   ✅ Dependencias instaladas correctamente.")


def check_env():
    """Verifica que existe el archivo .env con la API key."""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    example_path = os.path.join(os.path.dirname(__file__), ".env.example")

    if not os.path.exists(env_path):
        if os.path.exists(example_path):
            import shutil
            shutil.copy(example_path, env_path)
            print("\n⚠️  Se ha creado el archivo .env desde .env.example")
            print("   IMPORTANTE: Edita .env y pon tu clave API de OpenAI")
            print("   Puedes obtenerla en: https://platform.openai.com/api-keys\n")
            input("   Presiona ENTER cuando hayas añadido tu clave API...")
        else:
            print("\n❌ No se encontró .env ni .env.example")
            print("   Crea un archivo .env con: OPENAI_API_KEY=sk-tu-clave-aqui\n")
            sys.exit(1)

    # Verificar que la key no está vacía
    from dotenv import load_dotenv
    load_dotenv(env_path)
    key = os.getenv("OPENAI_API_KEY", "")
    if not key or key == "sk-tu-clave-api-aqui":
        print("\n⚠️  La clave API de OpenAI está vacía o es el valor por defecto.")
        print("   Edita el archivo .env y pon tu clave real.")
        print("   Puedes obtenerla en: https://platform.openai.com/api-keys\n")
        input("   Presiona ENTER cuando hayas añadido tu clave API...")


def create_dirs():
    """Crea directorios necesarios."""
    dirs = ["audio_cache", "data"]
    for d in dirs:
        os.makedirs(os.path.join(os.path.dirname(__file__), d), exist_ok=True)


def main():
    print()
    print("╔══════════════════════════════════════════════════╗")
    print("║      🤖 J.A.R.V.I.S. — Sistema de Arranque     ║")
    print("║         Asistente Personal de IA en Español      ║")
    print("║            Motor: OpenAI GPT-4o                  ║")
    print("╚══════════════════════════════════════════════════╝")
    print()

    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    check_dependencies()
    check_env()
    create_dirs()

    print("\n🚀 Iniciando JARVIS...")
    print("   Abre tu navegador en: http://localhost:8000\n")

    # Intentar abrir el navegador automáticamente
    import threading
    import webbrowser
    threading.Timer(2.0, lambda: webbrowser.open("http://localhost:8000")).start()

    # Arrancar servidor
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
