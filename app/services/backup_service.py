from __future__ import annotations

import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path

from app.db import BACKUP_DIR, DATA_DIR, DB_PATH, execute, get_setting

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def create_local_backup() -> Path:
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    zip_path = BACKUP_DIR / f"backup_ristorante_{stamp}.zip"

    # Utilizza l'API nativa SQLite Online Backup per garantire integrità totale
    temp_db = BACKUP_DIR / f"restaurant_quotes_{stamp}.db"
    if DB_PATH.exists():
        with sqlite3.connect(DB_PATH) as src_conn:
            with sqlite3.connect(temp_db) as dst_conn:
                src_conn.backup(dst_conn)

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        if temp_db.exists():
            zf.write(temp_db, arcname="restaurant_quotes.db")
        pdf_dir = DATA_DIR / "pdfs"
        if pdf_dir.exists():
            for pdf in pdf_dir.glob("*.pdf"):
                zf.write(pdf, arcname=f"pdfs/{pdf.name}")
    if temp_db.exists():
        temp_db.unlink(missing_ok=True)

    execute(
        "INSERT INTO backup_jobs(backup_type, file_path, status) VALUES (?, ?, ?)",
        ("local", str(zip_path), "created"),
    )
    return zip_path


def upload_to_google_drive(file_path: Path) -> str | None:
    enabled = get_setting("drive_backup_enabled", "false").lower() == "true"
    credentials_file = Path(__file__).resolve().parent.parent / "secrets" / "google_credentials.json"
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
