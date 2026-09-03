from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
VENV_DIR = BASE_DIR / ".venv"
VENV_PYTHON = VENV_DIR / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
IN_VENV = sys.prefix != sys.base_prefix

# Se non siamo dentro il virtualenv:
if not IN_VENV:
    # Se il virtualenv non esiste, crealo e installa i requirements
    if not VENV_PYTHON.exists():
        print("=" * 70)
        print("Configurazione primo avvio: creazione ambiente virtuale...")
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])
        pip_exe = VENV_DIR / ("Scripts/pip.exe" if sys.platform == "win32" else "bin/pip")
        req_file = BASE_DIR / "requirements.txt"
        if req_file.exists():
            print("Installazione dipendenze in corso...")
            subprocess.check_call([str(pip_exe), "install", "-r", str(req_file)])
        print("Ambiente configurato con successo!")
        print("=" * 70)
    # Riavvia il processo con l'interprete del virtualenv
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), *sys.argv])

import socket
import uvicorn

HOST = "127.0.0.1"


def find_available_port(host: str = "127.0.0.1", start_port: int = 8000) -> int:
    port = start_port
    while port < start_port + 50:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((host, port))
                return port
            except OSError:
                port += 1
    return start_port


PORT = find_available_port(HOST, 8000)
URL = f"http://{HOST}:{PORT}"


def open_browser() -> None:
    time.sleep(1.2)
    webbrowser.open(URL)


if __name__ == "__main__":
    print("=" * 70)
    print("Tenuta Turrita Quote Manager")
    print(f"Avvio applicazione locale su: {URL}")
    print("Premi CTRL+C per arrestare il server.")
    print("=" * 70)

    threading.Thread(target=open_browser, daemon=True).start()

    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=PORT,
        reload=False,
    )
