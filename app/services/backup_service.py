from __future__ import annotations

import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path

from app.db import execute, get_setting
from app.paths import BACKUP_DIR, DATA_DIR, DB_PATH, PDF_DIR, SECRETS_DIR

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def create_local_backup() -> Path:
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = BACKUP_DIR / f"backup_ristorante_{stamp}.zip"

    # Utilizza l'API nativa SQLite Online Backup per garantire integrità totale
    temp_db = BACKUP_DIR / f"restaurant_quotes_{stamp}.db"
    if DB_PATH.exists():
        src_conn = sqlite3.connect(DB_PATH)
        dst_conn = sqlite3.connect(temp_db)
        try:
            src_conn.backup(dst_conn)
        finally:
            dst_conn.close()
            src_conn.close()

    try:
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            if temp_db.exists():
                zf.write(temp_db, arcname="restaurant_quotes.db")
            pdf_dir = DATA_DIR / "pdfs"
            if pdf_dir.exists():
                for pdf in pdf_dir.glob("*.pdf"):
                    zf.write(pdf, arcname=f"pdfs/{pdf.name}")
    finally:
        if temp_db.exists():
            try:
                temp_db.unlink()
            except Exception:
                pass

    execute(
        "INSERT INTO backup_jobs(backup_type, file_path, status) VALUES (?, ?, ?)",
        ("local", str(zip_path), "created"),
    )
    return zip_path


def upload_to_google_drive(file_path: Path) -> str | None:
    enabled = get_setting("drive_backup_enabled", "false").lower() == "true"
    credentials_file = SECRETS_DIR / "google_credentials.json"
    token_file = DATA_DIR / "google_token.json"

    if not enabled or not credentials_file.exists():
        return None

    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except Exception as exc:
        raise RuntimeError("Librerie Google Drive non installate") from exc

    creds = None
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_file), SCOPES)
            creds = flow.run_local_server(port=0)
        token_file.write_text(creds.to_json(), encoding="utf-8")

    service = build("drive", "v3", credentials=creds)

    folder_name = "TenutaTurrita_Backup"
    results = service.files().list(
        q=f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false",
        spaces="drive",
        fields="files(id, name)",
    ).execute()
    folders = results.get("files", [])
    if folders:
        folder_id = folders[0]["id"]
    else:
        folder = service.files().create(
            body={"name": folder_name, "mimeType": "application/vnd.google-apps.folder"},
            fields="id",
        ).execute()
        folder_id = folder["id"]

    media = MediaFileUpload(str(file_path), mimetype="application/zip", resumable=True)
    uploaded = service.files().create(
        body={"name": file_path.name, "parents": [folder_id]},
        media_body=media,
        fields="id",
    ).execute()
    return uploaded.get("id")


def create_backup_with_optional_drive() -> tuple[Path, str | None, str | None]:
    zip_path = create_local_backup()
    drive_id = None
    error = None
    try:
        drive_id = upload_to_google_drive(zip_path)
        if drive_id:
            execute(
                "INSERT INTO backup_jobs(backup_type, file_path, google_drive_file_id, status) VALUES (?, ?, ?, ?)",
                ("google_drive", str(zip_path), drive_id, "uploaded"),
            )
    except Exception as exc:
        error = str(exc)
        execute(
            "INSERT INTO backup_jobs(backup_type, file_path, status, error_message) VALUES (?, ?, ?, ?)",
            ("google_drive", str(zip_path), "failed", error),
        )
    return zip_path, drive_id, error


def restore_from_backup_zip(zip_path: Path | str) -> dict[str, Any]:
    import shutil
    from typing import Any

    zip_path = Path(zip_path)
    if not zip_path.exists():
        raise FileNotFoundError(f"Il file di backup non esiste: {zip_path.name}")
    if not zipfile.is_zipfile(zip_path):
        raise ValueError("Il file specificato non è un archivio compresso ZIP valido.")

    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    temp_extract_dir = BACKUP_DIR / f"temp_restore_{stamp}"
    temp_extract_dir.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            namelist = zf.namelist()
            # Cerca il database SQLite nell'archivio
            db_entry = next(
                (name for name in namelist if name == "restaurant_quotes.db" or name.endswith("/restaurant_quotes.db")),
                None,
            )
            if not db_entry:
                raise ValueError("L'archivio ZIP non contiene il database essenziale 'restaurant_quotes.db'.")

            zf.extractall(temp_extract_dir)

        extracted_db = temp_extract_dir / db_entry

        # Verifica integrità strutturale SQLite del file estratto
        test_conn = sqlite3.connect(extracted_db)
        try:
            check = test_conn.execute("PRAGMA integrity_check").fetchone()
            if not check or check[0].lower() != "ok":
                raise ValueError(f"Controllo integrità del database fallito: {check[0] if check else 'Errore sconosciuto'}")
        finally:
            test_conn.close()

        # Backup di sicurezza pre-ripristino dello stato corrente
        if DB_PATH.exists():
            safety_backup = BACKUP_DIR / f"pre_restore_safety_{stamp}.db"
            cur_conn = sqlite3.connect(DB_PATH)
            saf_conn = sqlite3.connect(safety_backup)
            try:
                cur_conn.backup(saf_conn)
            finally:
                saf_conn.close()
                cur_conn.close()

        # Ripristino atomico del database tramite SQLite Online Backup API
        src_conn = sqlite3.connect(extracted_db)
        dst_conn = sqlite3.connect(DB_PATH)
        try:
            src_conn.backup(dst_conn)
            dst_conn.commit()
        finally:
            dst_conn.close()
            src_conn.close()

        # Ripristino dei file PDF contenuti nell'archivio
        extracted_pdfs = temp_extract_dir / "pdfs"
        pdf_count = 0
        if extracted_pdfs.exists() and extracted_pdfs.is_dir():
            PDF_DIR.mkdir(parents=True, exist_ok=True)
            for pdf_file in extracted_pdfs.glob("*.pdf"):
                dest_pdf = PDF_DIR / pdf_file.name
                shutil.copy2(pdf_file, dest_pdf)
                pdf_count += 1

        # Esecuzione automatica migrazioni dello schema per garantire compatibilità con versioni software recenti
        from app.db import init_db

        init_db()

        # Registrazione nei log di backup
        execute(
            "INSERT INTO backup_jobs(backup_type, file_path, status) VALUES (?, ?, ?)",
            ("restore", str(zip_path), "restored"),
        )

        return {
            "restored": True,
            "backup_file": zip_path.name,
            "pdf_count": pdf_count,
            "restored_at": stamp,
        }

    finally:
        if temp_extract_dir.exists():
            shutil.rmtree(temp_extract_dir, ignore_errors=True)

