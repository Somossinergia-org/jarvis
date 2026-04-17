@echo off
chcp 65001 >nul
title J.A.R.V.I.S. - Instalador y Arrancador
color 0B

echo.
echo ╔══════════════════════════════════════════════════╗
echo ║      J.A.R.V.I.S. - Sistema de Arranque         ║
echo ║      Asistente Personal de IA en Español         ║
echo ╚══════════════════════════════════════════════════╝
echo.

:: ─── Buscar Python automáticamente ───────────────────────────────────────
set PYTHON_EXE=

:: 1) python en PATH estándar
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_EXE=python
    goto :python_found
)

:: 2) py launcher (instalador oficial de python.org)
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_EXE=py
    goto :python_found
)

:: 3) Python 3.12 / 3.11 / 3.10 en ubicaciones habituales
for %%V in (312 311 310 39) do (
    if exist "C:\Python%%V\python.exe" (
        set PYTHON_EXE=C:\Python%%V\python.exe
        goto :python_found
    )
    if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" (
        set PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe
        goto :python_found
    )
)

:: 4) Conda / Miniconda / Anaconda
for %%P in (
    "%USERPROFILE%\miniconda3\python.exe"
    "%USERPROFILE%\anaconda3\python.exe"
    "C:\ProgramData\miniconda3\python.exe"
    "C:\ProgramData\Anaconda3\python.exe"
) do (
    if exist %%P (
        set PYTHON_EXE=%%P
        goto :python_found
    )
)

echo.
echo  ❌  ERROR: Python no encontrado en este equipo.
echo      Descargalo de: https://www.python.org/downloads/
echo      IMPORTANTE: Al instalar, marca "Add Python to PATH"
echo.
pause
exit /b 1

:python_found
echo  ✅  Python encontrado: %PYTHON_EXE%
%PYTHON_EXE% --version

:: ─── Instalar dependencias ────────────────────────────────────────────────
echo.
echo [2/3] Instalando dependencias (puede tardar 1-2 minutos)...
%PYTHON_EXE% -m pip install -r "%~dp0requirements.txt" --quiet
if %errorlevel% neq 0 (
    echo.
    echo  ⚠️  Error al instalar dependencias. Revisa tu conexión a internet.
    pause
    exit /b 1
)
echo  ✅  Dependencias instaladas.

:: ─── Arrancar JARVIS ──────────────────────────────────────────────────────
echo.
echo [3/3] Arrancando JARVIS...
echo.
echo ========================================
echo   JARVIS se abrira en tu navegador
echo   en http://localhost:8000
echo.
echo   Para parar JARVIS, cierra esta ventana
echo ========================================
echo.

cd /d "%~dp0"
:: Pequeño delay para que el servidor levante antes de abrir el navegador
timeout /t 2 /nobreak >nul
start "" http://localhost:8000
%PYTHON_EXE% -m uvicorn server:app --host 0.0.0.0 --port 8000

pause
