from __future__ import annotations

import threading
import time
import webbrowser

import uvicorn


HOST = "127.0.0.1"
PORT = 8001
URL = f"http://{HOST}:{PORT}"


def open_browser() -> None:
    time.sleep(1.5)
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
