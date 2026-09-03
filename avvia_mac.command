#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "======================================================================"
echo " TENUTA TURRITA - GESTIONALE PREVENTIVI (MACOS)"
echo "======================================================================"
echo ""

# Verifica presenza di Python 3
if ! command -v python3 >/dev/null 2>&1; then
    echo "[INFO] Python 3 non rilevato su macOS. Preparazione installazione..."
    if command -v brew >/dev/null 2>&1; then
        echo "[INFO] Installazione tramite Homebrew in corso..."
        brew install python3
    else
        echo "[INFO] Download dell'installer ufficiale Python per macOS..."
        PKG_PATH="/tmp/python-macos.pkg"
        curl -sSL "https://www.python.org/ftp/python/3.12.5/python-3.12.5-macos11.pkg" -o "$PKG_PATH"
        echo "[INFO] Apertura installer ufficiale Python. Completa l'installazione guidata."
        open -W "$PKG_PATH"
    fi
fi

# Avvio tramite launcher intelligente
python3 run_local.py
