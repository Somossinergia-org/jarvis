' ============================================================
'  J.A.R.V.I.S. - Arranque silencioso al inicio de Windows
'  No muestra ninguna ventana de CMD
' ============================================================
Dim oShell
Set oShell = CreateObject("WScript.Shell")

Dim projectDir
projectDir = "C:\Users\orihu\OneDrive\Escritorio\jarvis"

' 1) Arrancar el servidor con Python 3.12 en segundo plano (ventana oculta)
oShell.Run "cmd /c set PYTHONUTF8=1 && cd /d """ & projectDir & """ && py -3.12 -m uvicorn server:app --host 0.0.0.0 --port 8000 > """ & projectDir & "\jarvis.log"" 2>&1", 0, False

' 2) Esperar 4 segundos para que el servidor levante
WScript.Sleep 4000

' 3) Abrir el navegador en la interfaz de JARVIS
oShell.Run "http://localhost:8000"

Set oShell = Nothing
