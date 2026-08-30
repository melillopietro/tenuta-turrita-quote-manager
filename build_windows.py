from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def ensure_icon() -> Path | None:
    icon_path = BASE_DIR / "app" / "static" / "app_icon.ico"
    png_path = BASE_DIR / "app" / "static" / "tenuta_turrita_logo.png"

    if icon_path.exists():
        return icon_path

    if png_path.exists():
        try:
            from PIL import Image

            img = Image.open(png_path)
            icon_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(
                icon_path,
                format="ICO",
                sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)],
            )
            print(f"[INFO] Icona Windows generata: {icon_path}")
            return icon_path
        except Exception as exc:
            print(f"[AVVISO] Impossibile generare icona: {exc}")

    return None


def build(onefile: bool = True) -> None:
    print("=" * 70)
    print(" TENUTA TURRITA - COMPILAZIONE ESEGUIBILE WINDOWS (.EXE)")
    print("=" * 70)

    try:
        import PyInstaller
    except ImportError:
        print("[INFO] Installazione PyInstaller in corso...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    icon_path = ensure_icon()
    icon_arg = ["--icon", str(icon_path)] if icon_path and icon_path.exists() else []

    mode_arg = ["--onefile"] if onefile else ["--onedir"]

    templates_dir = BASE_DIR / "app" / "templates"
    static_dir = BASE_DIR / "app" / "static"

    sep = ";" if sys.platform == "win32" else ":"

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
        f"{templates_dir}{sep}app/templates",
        "--add-data",
        f"{static_dir}{sep}app/static",
        "--collect-all",
        "uvicorn",
        "--collect-all",
        "fastapi",
        "--collect-all",
        "reportlab",
        "--collect-all",
        "starlette",
        "--collect-all",
        "jinja2",
        "--hidden-import",
        "anyio",
        "--hidden-import",
        "email",
        "--hidden-import",
        "sqlite3",
        "--hidden-import",
        "multiprocessing",
        "desktop_app.py",
    ]

    print("[INFO] Esecuzione comando PyInstaller...")
    subprocess.check_call(cmd, cwd=BASE_DIR)

    dist_dir = BASE_DIR / "dist"
    print("\n" + "=" * 70)
    print(" [OK] Compilazione completata con successo!")
    print(f" Output: {dist_dir}")
    print("=" * 70)


if __name__ == "__main__":
    is_onefile = "--onedir" not in sys.argv
    build(onefile=is_onefile)

