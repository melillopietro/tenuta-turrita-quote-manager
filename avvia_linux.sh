#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "======================================================================"
echo " TENUTA TURRITA - GESTIONALE PREVENTIVI (LINUX)"
echo "======================================================================"
echo ""

# Verifica presenza di Python 3
if ! command -v python3 >/dev/null 2>&1; then
    echo "[INFO] Python 3 non trovato. Tentativo di installazione automatica..."
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update && sudo apt-get install -y python3 python3-venv python3-pip
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y python3 python3-pip
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -Sy --noconfirm python python-pip
    elif command -v zypper >/dev/null 2>&1; then
        sudo zypper install -y python3 python3-pip
    else
        echo "[ERRORE] Gestore di pacchetti non riconosciuto. Installa Python 3 manualmente."
        exit 1
    fi
fi

# Verifica supporto venv
if ! python3 -c "import venv" >/dev/null 2>&1; then
    echo "[INFO] Modulo python3-venv mancante. Installazione in corso..."
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update && sudo apt-get install -y python3-venv
    fi
fi

# Avvio tramite launcher intelligente
python3 run_local.py
