"""
J.A.R.V.I.S. v4.0 ULTRA — Lanzador nativo (sin Chrome)
Ejecuta JARVIS como una aplicacion de escritorio real.
Doble clic en start_jarvis.bat para arrancar.
"""
import sys
import os
import threading
import time

# Asegurar directorio correcto
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def start_server():
    """Arranca el servidor FastAPI en segundo plano."""
    import uvicorn
    uvicorn.run(
        "server:app",
        host="127.0.0.1",
        port=8000,
        log_level="error",
        access_log=False,
    )

def wait_for_server(timeout=15):
    """Espera a que el servidor este listo antes de abrir la ventana."""
    import urllib.request
    for _ in range(timeout * 5):
        try:
            urllib.request.urlopen("http://127.0.0.1:8000", timeout=1)
            return True
        except Exception:
            time.sleep(0.2)
    return False

if __name__ == "__main__":
    print("=" * 50)
    print("  J.A.R.V.I.S. v4.0 ULTRA — Iniciando...")
    print("=" * 50)

    # Arrancar servidor en hilo daemon
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    print("  [*] Servidor iniciando...")

    # Esperar servidor
    if not wait_for_server():
        print("  [!] Error: el servidor no arranco en tiempo.")
        sys.exit(1)
    print("  [*] Servidor listo en http://127.0.0.1:8000")

    # Abrir ventana nativa
    try:
        import webview
        print("  [*] Abriendo ventana JARVIS...")
        window = webview.create_window(
            title="J.A.R.V.I.S. ULTRA v4.0",
            url="http://127.0.0.1:8000",
            width=1280,
            height=800,
            resizable=True,
            fullscreen=False,
            min_size=(900, 600),
            background_color="#020a12",
            text_select=False,
            confirm_close=False,
        )
        # Iniciar con opcion de depuracion en dev, sin ella en prod
        webview.start(debug=False)
    except ImportError:
        print("  [!] pywebview no instalado. Abriendo en navegador...")
        import webbrowser
        webbrowser.open("http://127.0.0.1:8000")
        input("Presiona Enter para cerrar JARVIS...")
    except Exception as e:
        print(f"  [!] Error al abrir ventana: {e}")
        import webbrowser
        webbrowser.open("http://127.0.0.1:8000")
        input("Presiona Enter para cerrar JARVIS...")
