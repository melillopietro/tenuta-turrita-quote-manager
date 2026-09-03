@echo off
chcp 65001 >nul
title Tenuta Turrita - Gestionale Preventivi

cd /d "%~dp0"

echo ======================================================================
echo  TENUTA TURRITA - GESTIONALE PREVENTIVI E RICEVIMENTI
echo ======================================================================
echo.

REM Se l'ambiente virtuale non esiste, esegui lo script di auto-provisioning PowerShell
if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Primo avvio su Windows: avvio configurazione automatica...
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\setup_windows.ps1"
    if %errorlevel% neq 0 (
        echo.
        echo [ERRORE] La configurazione automatica di Python ha riscontrato un problema.
        pause
        exit /b 1
    )
)

echo [INFO] Avvio applicazione desktop Tenuta Turrita...
.venv\Scripts\python.exe desktop_app.py

if %errorlevel% neq 0 (
    echo.
    echo [ERRORE] Si e verificato un problema durante l'esecuzione dell'applicazione.
    pause
)
