from __future__ import annotations

import sys
from pathlib import Path

# Se l'applicazione è compilata con PyInstaller (frozen executable)
IS_FROZEN = getattr(sys, "frozen", False)

if IS_FROZEN:
    # Directory dove si trova l'eseguibile .exe (per dati persistenti: database, pdf, backup)
    BASE_DIR = Path(sys.executable).resolve().parent
    # Directory dove PyInstaller estrae le risorse statiche e template
    BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", BASE_DIR))
    APP_DIR = BUNDLE_DIR / "app" if (BUNDLE_DIR / "app").exists() else BUNDLE_DIR
else:
    BASE_DIR = Path(__file__).resolve().parent.parent
    APP_DIR = Path(__file__).resolve().parent

# Directory dati persistenti
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "restaurant_quotes.db"
PDF_DIR = DATA_DIR / "pdfs"
BACKUP_DIR = DATA_DIR / "backups"
SECRETS_DIR = BASE_DIR / "app" / "secrets" if (BASE_DIR / "app" / "secrets").exists() else APP_DIR / "secrets"

# Risorse statiche e template
STATIC_DIR = APP_DIR / "static"
TEMPLATES_DIR = APP_DIR / "templates"
LOGO_PATH = STATIC_DIR / "tenuta_turrita_logo.png"

# Assicura creazione cartelle dati
DATA_DIR.mkdir(parents=True, exist_ok=True)
PDF_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
