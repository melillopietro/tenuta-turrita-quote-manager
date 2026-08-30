from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Iterable

from app.paths import BACKUP_DIR, BASE_DIR, DATA_DIR, DB_PATH, PDF_DIR


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def query_one(sql: str, params: Iterable[Any] = ()) -> sqlite3.Row | None:
    with get_connection() as conn:
        cur = conn.execute(sql, tuple(params))
        return cur.fetchone()


def query_all(sql: str, params: Iterable[Any] = ()) -> list[sqlite3.Row]:
    with get_connection() as conn:
        cur = conn.execute(sql, tuple(params))
        return cur.fetchall()


def execute(sql: str, params: Iterable[Any] = ()) -> int:
    with get_connection() as conn:
        cur = conn.execute(sql, tuple(params))
        conn.commit()
        return int(cur.lastrowid)


def init_db() -> None:
    schema = """
    CREATE TABLE IF NOT EXISTS quote_counters (
        year INTEGER PRIMARY KEY,
        last_number INTEGER NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        address TEXT,
        fiscal_code TEXT,
        notes TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS staff (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT,
        email TEXT,
        active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS quotes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quote_number TEXT NOT NULL UNIQUE,
        year INTEGER NOT NULL,
        progressive_number INTEGER NOT NULL,
        customer_id INTEGER NOT NULL,
        event_type TEXT NOT NULL,
        custom_event_type TEXT,
        event_date TEXT,
        event_start_time TEXT,
        event_end_time TEXT,
        guests_adults INTEGER NOT NULL DEFAULT 0,
        guests_children INTEGER NOT NULL DEFAULT 0,
        location TEXT,
        status TEXT NOT NULL DEFAULT 'bozza',
        compiled_by_staff_id INTEGER,
        price_per_adult REAL NOT NULL DEFAULT 0,
        price_per_child REAL NOT NULL DEFAULT 0,
        extra_amount REAL NOT NULL DEFAULT 0,
        discount_amount REAL NOT NULL DEFAULT 0,
        vat_rate REAL NOT NULL DEFAULT 0,
        total_amount REAL NOT NULL DEFAULT 0,
        notes TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(customer_id) REFERENCES customers(id) ON DELETE CASCADE,
        FOREIGN KEY(compiled_by_staff_id) REFERENCES staff(id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS quote_menu_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quote_id INTEGER NOT NULL,
        course_type TEXT NOT NULL,
        custom_course_name TEXT,
        dish_name TEXT NOT NULL,
        description TEXT,
        allergens TEXT,
        notes TEXT,
        is_extra INTEGER NOT NULL DEFAULT 0,
        extra_price REAL NOT NULL DEFAULT 0,
        display_order INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY(quote_id) REFERENCES quotes(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS quote_contracts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quote_id INTEGER NOT NULL UNIQUE,
        iban TEXT,
        account_holder TEXT,
        deposit_amount REAL NOT NULL DEFAULT 0,
        deposit_due_date TEXT,
        quote_expiry_date TEXT,
        guest_confirmation_date TEXT,
        balance_due_date TEXT,
        cancellation_deadline TEXT,
        cancellation_policy TEXT,
        penalty_clause TEXT,
        contract_text TEXT,
        accepted_at TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(quote_id) REFERENCES quotes(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS quote_pdfs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quote_id INTEGER NOT NULL,
        file_path TEXT NOT NULL,
        generated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(quote_id) REFERENCES quotes(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS email_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quote_id INTEGER NOT NULL,
        recipient_email TEXT NOT NULL,
        subject TEXT NOT NULL,
        sent_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        status TEXT NOT NULL,
        error_message TEXT,
        FOREIGN KEY(quote_id) REFERENCES quotes(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS app_settings (
        key TEXT PRIMARY KEY,
        value TEXT
    );

    CREATE TABLE IF NOT EXISTS backup_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        backup_type TEXT NOT NULL,
        file_path TEXT NOT NULL,
        google_drive_file_id TEXT,
        status TEXT NOT NULL,
        error_message TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """
    with get_connection() as conn:
        conn.executescript(schema)

        # ROLE / CHILD MENU MIGRATION
        quote_cols_role_patch = {row["name"] for row in conn.execute("PRAGMA table_info(quotes)").fetchall()}
        if "primary_customer_role" not in quote_cols_role_patch:
            conn.execute("ALTER TABLE quotes ADD COLUMN primary_customer_role TEXT")

        menu_cols_role_patch = {row["name"] for row in conn.execute("PRAGMA table_info(quote_menu_items)").fetchall()}
        if "menu_group" not in menu_cols_role_patch:
            conn.execute("ALTER TABLE quote_menu_items ADD COLUMN menu_group TEXT NOT NULL DEFAULT 'adult'")

        # Migrazione non distruttiva: campi per secondo cliente / sposi.
        quote_cols = {row["name"] for row in conn.execute("PRAGMA table_info(quotes)").fetchall()}
        new_quote_columns = {
            "secondary_customer_role": "TEXT",
            "secondary_customer_first_name": "TEXT",
            "secondary_customer_last_name": "TEXT",
            "secondary_customer_phone": "TEXT",
            "secondary_customer_email": "TEXT",
        }
        for col, definition in new_quote_columns.items():
            if col not in quote_cols:
                conn.execute(f"ALTER TABLE quotes ADD COLUMN {col} {definition}")

        conn.commit()

    # Default settings
    default_settings = {
        "company_name": "Tenuta Turrita",
        "company_address": "Via Roma, Dragoni (CE)",
        "company_phone": "+39 320 688 3788",
        "company_email": "",
        "company_iban": "",
        "company_account_holder": "Tenuta Turrita",
        "company_payoff": "Villa per matrimoni ed eventi",
        "default_contract_terms": """Il presente preventivo ha validità di 15 giorni dalla data di emissione.

La prenotazione della data evento si intende confermata esclusivamente a seguito di accettazione del preventivo e versamento dell'acconto concordato.

Il numero definitivo degli ospiti dovrà essere comunicato entro i termini concordati con la struttura.

Eventuali modifiche al menù, agli allestimenti o ai servizi accessori potranno comportare una variazione dell'importo finale.

Il saldo dovrà essere corrisposto secondo le modalità concordate con la direzione.

La struttura si riserva di valutare eventuali modifiche organizzative necessarie per garantire il corretto svolgimento dell'evento.""",
        "smtp_host": "",
        "smtp_port": "587",
        "smtp_secure": "false",
        "smtp_username": "",
        "smtp_password": "",
        "smtp_sender_name": "Tenuta Turrita",
        "smtp_sender_email": "",
        "drive_backup_enabled": "false",
    }
    with get_connection() as conn:
        for key, value in default_settings.items():
            conn.execute(
                "INSERT OR IGNORE INTO app_settings(key, value) VALUES (?, ?)",
                (key, value),
            )
        existing_staff = conn.execute("SELECT COUNT(*) AS c FROM staff").fetchone()["c"]
        if existing_staff == 0:
            conn.execute("INSERT INTO staff(name, role, email) VALUES (?, ?, ?)", ("Direzione", "Responsabile eventi", ""))
        conn.commit()


def get_setting(key: str, default: str = "") -> str:
    row = query_one("SELECT value FROM app_settings WHERE key = ?", (key,))
    return str(row["value"]) if row and row["value"] is not None else default


def set_setting(key: str, value: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO app_settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        conn.commit()


def settings_dict() -> dict[str, str]:
    rows = query_all("SELECT key, value FROM app_settings ORDER BY key")
    return {row["key"]: row["value"] or "" for row in rows}
