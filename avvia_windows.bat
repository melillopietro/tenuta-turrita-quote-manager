@echo off
chcp 65001 >nul
title Tenuta Turrita - Gestionale Preventivi

echo ======================================================================
echo  TENUTA TURRITA - GESTIONALE PREVENTIVI E RICEVIMENTI
echo ======================================================================
echo.

cd /d "%~dp0"

REM Verifica se esiste l'ambiente virtuale .venv
if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Primo avvio su Windows: creazione ambiente virtuale in corso...
    where python >nul 2>nul
    if %errorlevel% neq 0 (
        where py >nul 2>nul
        if %errorlevel% neq 0 (
            echo [ERRORE] Python non trovato nel sistema.
            echo Scarica e installa Python da https://www.python.org/downloads/
            echo Ricordati di selezionare la casella "Add Python to PATH" durante l'installazione.
            pause
            exit /b 1
        ) else (
            py -3 -m venv .venv
        )
    ) else (
        python -m venv .venv
    )

    echo [INFO] Installazione dipendenze in corso...
    .venv\Scripts\python.exe -m pip install --upgrade pip
    .venv\Scripts\python.exe -m pip install -r requirements.txt
    echo [INFO] Configurazione completata!
    echo.
)

echo [INFO] Avvio applicazione desktop Tenuta Turrita...
.venv\Scripts\python.exe desktop_app.py

if %errorlevel% neq 0 (
    echo.
    echo [ERRORE] Si e verificato un problema durante l'esecuzione.
    pause
)
