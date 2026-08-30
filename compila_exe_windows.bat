@echo off
chcp 65001 >nul
title Compilazione EXE Windows - Tenuta Turrita

echo ======================================================================
echo  TENUTA TURRITA - COMPILAZIONE ESEGUIBILE (.EXE) PER WINDOWS
echo ======================================================================
echo.

cd /d "%~dp0"

REM Verifica esistenza virtualenv
if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Creazione ambiente virtuale per la compilazione...
    python -m venv .venv
    .venv\Scripts\python.exe -m pip install -r requirements.txt
)

echo [INFO] Installazione PyInstaller...
.venv\Scripts\python.exe -m pip install pyinstaller

echo [INFO] Avvio compilazione eseguibile autonomo...
.venv\Scripts\python.exe build_windows.py

echo.
echo ======================================================================
echo  Compilazione terminata!
echo  L'eseguibile pronto si trova nella cartella "dist\TenutaTurritaQuoteManager.exe"
echo ======================================================================
echo.
pause
