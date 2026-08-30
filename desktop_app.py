from __future__ import annotations

import multiprocessing
import os
import sys
import threading
import time
import webbrowser

# Freeze support per Windows PyInstaller
if __name__ == "__main__":
    multiprocessing.freeze_support()

import uvicorn
from app.db import init_db
from app.main import app

HOST = "127.0.0.1"
PORT = 8000
URL = f"http://{HOST}:{PORT}"


def open_browser() -> None:
    time.sleep(1.2)
    try:
        webbrowser.open(URL)
    except Exception as exc:
        print(f"Impossibile aprire automaticamente il browser: {exc}")


def main() -> None:
    print("=" * 68)
    print(" TENUTA TURRITA - GESTIONALE PREVENTIVI & EVENTI")
    print("=" * 68)
    print(f" Avvio del server desktop in corso...")
    print(f" Accesso locale: {URL}")
    print(" Per arrestare l'applicazione, chiudi questa finestra.")
    print("=" * 68)

    # Inizializza il database SQLite locale
    init_db()

    # Avvia l'apertura automatica del browser
    threading.Thread(target=open_browser, daemon=True).start()

    # Avvio Uvicorn passando direttamente l'istanza FastAPI
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="info",
        access_log=False,
    )


if __name__ == "__main__":
    main()
