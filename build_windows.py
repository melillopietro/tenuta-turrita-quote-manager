from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def build(onefile: bool = True) -> None:
    print("=" * 70)
    print(" Compilazione Eseguibile Windows (.exe) - Tenuta Turrita")
    print("=" * 70)

    try:
        import PyInstaller
    except ImportError:
        print("Installazione di PyInstaller in corso...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    sep = ";" if sys.platform == "win32" else ":"

    icon_path = BASE_DIR / "app" / "static" / "app_icon.ico"
    icon_arg = ["--icon", str(icon_path)] if icon_path.exists() else []

    mode_arg = ["--onefile"] if onefile else ["--onedir"]

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        *mode_arg,
        "--name",
        "TenutaTurritaQuoteManager",
        "--clean",
        *icon_arg,
        "--add-data",
        f"app/templates{sep}app/templates",
        "--add-data",
        f"app/static{sep}app/static",
        "--hidden-import",
        "uvicorn.logging",
        "--hidden-import",
        "uvicorn.loops",
        "--hidden-import",
        "uvicorn.loops.auto",
        "--hidden-import",
        "uvicorn.protocols",
        "--hidden-import",
        "uvicorn.protocols.http",
        "--hidden-import",
        "uvicorn.protocols.http.auto",
        "--hidden-import",
        "uvicorn.protocols.http.h11_impl",
        "--hidden-import",
        "uvicorn.protocols.http.httptools_impl",
        "--hidden-import",
        "uvicorn.protocols.websockets",
        "--hidden-import",
        "uvicorn.protocols.websockets.auto",
        "--hidden-import",
        "uvicorn.protocols.websockets.wsproto_impl",
        "--hidden-import",
        "uvicorn.protocols.websockets.websockets_impl",
        "--hidden-import",
        "uvicorn.lifespans",
        "--hidden-import",
        "uvicorn.lifespans.on",
        "--hidden-import",
        "uvicorn.lifespans.off",
        "--hidden-import",
        "reportlab",
        "--hidden-import",
        "reportlab.lib",
        "--hidden-import",
        "reportlab.platypus",
        "--hidden-import",
        "reportlab.pdfgen",
        "--hidden-import",
        "jinja2",
        "--hidden-import",
        "starlette",
        "--hidden-import",
        "fastapi",
        "--hidden-import",
        "anyio",
        "--hidden-import",
        "email",
        "--hidden-import",
        "sqlite3",
        "desktop_app.py",
    ]

    print(f"Esecuzione PyInstaller ({'--onefile' if onefile else '--onedir'})...")
    subprocess.check_call(cmd, cwd=BASE_DIR)

    dist_dir = BASE_DIR / "dist"
    print("
" + "=" * 70)
    print(" Compilazione completata con successo!")
    print(f" File generato in: {dist_dir}")
    print("=" * 70)


if __name__ == "__main__":
    is_onefile = "--onedir" not in sys.argv
    build(onefile=is_onefile)
