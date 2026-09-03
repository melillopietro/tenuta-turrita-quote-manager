from __future__ import annotations

import os
from pathlib import Path
import pytest
from starlette.testclient import TestClient

from app.db import DB_PATH, get_connection, init_db, query_all, query_one
from app.main import app
from app.services.backup_service import (
    create_backup_with_optional_drive,
    create_local_backup,
    restore_from_backup_zip,
)
from app.services.pdf_service import build_pdf
from app.services.quote_service import (
    MENU_PRESETS,
    calculate_quote_breakdown,
    create_quote,
    delete_quote,
    duplicate_quote,
    get_quote,
    get_quote_items,
    list_quotes,
    update_quote,
    update_quote_status,
)


@pytest.fixture(autouse=True)
def setup_database():
    init_db()


def test_calculate_quote_breakdown():
    # 100 adulti @ 150€ = 15.000€
    # 10 bambini @ 50€ = 500€
    # Extra: 500€, Sconto: 1.000€
    # Imponibile netto: 15.000 + 500 + 500 - 1.000 = 15.000€
    # IVA 10% = 1.500€
    # Totale = 16.500€
    res = calculate_quote_breakdown(
        guests_adults=100,
        guests_children=10,
        price_per_adult=150.0,
        price_per_child=50.0,
        extra_amount=500.0,
        discount_amount=1000.0,
        vat_rate=10.0,
    )
    assert res["adults_subtotal"] == 15000.0
    assert res["children_subtotal"] == 500.0
    assert res["extra_amount"] == 500.0
    assert res["discount_amount"] == 1000.0
    assert res["net_taxable"] == 15000.0
    assert res["vat_amount"] == 1500.0
    assert res["total_amount"] == 16500.0


def test_quote_crud_and_duplication():
    # 1. Create quote
    quote_data = {
        "primary_customer_role": "Sposo",
        "customer_first_name": "Leonardo",
        "customer_last_name": "Da Vinci",
        "customer_phone": "+39 340 1122334",
        "customer_email": "leonardo@turrita.it",
        "customer_fiscal_code": "DVCLND80A01H501U",
        "customer_address": "Via del Genio 1, Firenze",
        "customer_notes": "Tavolo d'onore panoramico",
        "secondary_customer_role": "Sposa",
        "secondary_customer_first_name": "Monna",
        "secondary_customer_last_name": "Lisa",
        "event_type": "Matrimonio",
        "event_date": "2026-09-18",
        "event_start_time": "16:00",
        "event_end_time": "01:00",
        "guests_adults": 120,
        "guests_children": 15,
        "location": "Corte Principale",
        "price_per_adult": 160.0,
        "price_per_child": 50.0,
        "extra_amount": 800.0,
        "discount_amount": 500.0,
        "vat_rate": 10.0,
        "notes": "Taglio torta con spettacolo fontane luminose",
        "menu_group": ["adult", "adult", "children"],
        "course_type": ["Antipasto", "Primo", "Primo"],
        "custom_course_name": ["", "", ""],
        "dish_name": ["Crudo di Mare", "Risotto ai Porcini", "Penne al Pomodoro"],
        "description": ["Gamberi e scampi", "Con tartufo estivo", "Salsa fresca"],
        "allergens": ["Crostacei", "Latticini", "Glutine"],
        "item_notes": ["", "", "Bambini"],
        "extra_price": ["0", "0", "0"],
    }

    quote_id = create_quote(quote_data)
    assert quote_id > 0

    quote = get_quote(quote_id)
    assert quote is not None
    assert quote["first_name"] == "Leonardo"
    assert quote["last_name"] == "Da Vinci"
    assert quote["secondary_customer_first_name"] == "Monna"
    assert quote["guests_adults"] == 120
    assert quote["status"] == "bozza"

    items = get_quote_items(quote_id)
    assert len(items) == 3
    adult_items = [it for it in items if it["menu_group"] == "adult"]
    child_items = [it for it in items if it["menu_group"] == "children"]
    assert len(adult_items) == 2
    assert len(child_items) == 1

    # 2. Update status
    update_quote_status(quote_id, "accettato")
    updated_q = get_quote(quote_id)
    assert updated_q["status"] == "accettato"

    # 3. Duplicate quote
    dup_id = duplicate_quote(quote_id)
    assert dup_id != quote_id
    dup_q = get_quote(dup_id)
    assert dup_q["first_name"] == "Leonardo"
    assert dup_q["quote_number"] != quote["quote_number"]
    assert dup_q["status"] == "bozza"

    # 4. Delete duplicate
    delete_quote(dup_id)
    assert get_quote(dup_id) is None


def test_list_quotes_filters():
    quotes_all = list_quotes()
    assert len(quotes_all) >= 1

    # Search filter
    filtered_name = list_quotes(q="Leonardo")
    assert any(q["last_name"] == "Da Vinci" for q in filtered_name)

    filtered_none = list_quotes(q="NonEsistenteXYZZY")
    assert len(filtered_none) == 0

    # Status filter
    accepted = list_quotes(status="accettato")
    assert all(q["status"] == "accettato" for q in accepted)


def test_pdf_generation():
    quotes = list_quotes()
    assert len(quotes) > 0
    quote_id = quotes[0]["id"]

    pdf_path = build_pdf(quote_id)
    assert pdf_path.exists()
    assert pdf_path.suffix == ".pdf"
    assert pdf_path.stat().st_size > 1000

    # Verify standard PDF magic header
    with open(pdf_path, "rb") as f:
        header = f.read(5)
        assert header == b"%PDF-"


def test_backup_service():
    zip_path, drive_id, error = create_backup_with_optional_drive()
    assert zip_path.exists()
    assert zip_path.suffix == ".zip"
    assert zip_path.stat().st_size > 0
    job = query_one("SELECT * FROM backup_jobs ORDER BY id DESC LIMIT 1")
    assert job is not None


def test_fastapi_endpoints():
    client = TestClient(app)

    # Dashboard
    res = client.get("/")
    assert res.status_code == 200
    assert "Tenuta Turrita" in res.text

    # Quotes archive
    res = client.get("/quotes")
    assert res.status_code == 200
    assert "Preventivi" in res.text

    # Presets API
    res = client.get("/api/presets/matrimonio_grand_gala")
    assert res.status_code == 200
    preset_data = res.json()
    assert preset_data["name"] == "Matrimonio Grand Galà"
    assert len(preset_data["adult_items"]) > 0

    # New quote form
    res = client.get("/quotes/new")
    assert res.status_code == 200
    assert "Modelli Gastronomici Predefiniti" in res.text

    # Detail page
    quotes = list_quotes()
    quote_id = quotes[0]["id"]
    res = client.get(f"/quotes/{quote_id}")
    assert res.status_code == 200
    assert "Prospetto Economico Dettagliato" in res.text

    # Print view
    res = client.get(f"/quotes/{quote_id}/print")
    assert res.status_code == 200
    assert "Stampa Documento" in res.text

    # Email send page
    res = client.get(f"/quotes/{quote_id}/send")
    assert res.status_code == 200
    assert "Invia Preventivo" in res.text

    # PDF download route
    res = client.get(f"/quotes/{quote_id}/pdf")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"


def test_pdf_generation_with_xml_special_characters():
    quote_data = {
        "customer_first_name": "Mario & Luigi",
        "customer_last_name": "Rossi <Spouses>",
        "event_type": "Matrimonio",
        "event_date": "2026-10-15",
        "guests_adults": 80,
        "guests_children": 5,
        "price_per_adult": 120.0,
        "price_per_child": 40.0,
        "notes": "Taglio torta & brindisi con flute <oro & cristallo>.",
        "menu_group": ["adult"],
        "course_type": ["Primo"],
        "custom_course_name": [""],
        "dish_name": ["Spaghetti Mare & Monti <Specialità>"],
        "description": ["Con vongole & porcini freschi <km 0>"],
        "allergens": ["Glutine & Crostacei"],
        "item_notes": ["Servire caldo & fumante"],
        "extra_price": ["0"],
    }
    quote_id = create_quote(quote_data)
    pdf_path = build_pdf(quote_id)
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 1000


def test_database_wal_and_indexes():
    with get_connection() as conn:
        journal_mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert journal_mode.lower() == "wal"

        indexes = [r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()]
        assert "idx_quotes_customer_id" in indexes
        assert "idx_quotes_status" in indexes
        assert "idx_quotes_event_date" in indexes
        assert "idx_quote_menu_items_quote_id" in indexes


def test_404_error_handling():
    client = TestClient(app)

    res = client.get("/quotes/999999")
    assert res.status_code == 404
    assert "Preventivo non trovato" in res.text

    res = client.get("/quotes/999999/pdf")
    assert res.status_code == 404
    assert "Preventivo non trovato" in res.text

    res = client.get("/quotes/999999/print")
    assert res.status_code == 404
    assert "Preventivo non trovato" in res.text

    res = client.get("/backup/download/999999")
    assert res.status_code == 404
    assert "Archivio di backup non trovato" in res.text


def test_negative_input_sanitization():
    res = calculate_quote_breakdown(
        guests_adults=-10,
        guests_children=-5,
        price_per_adult=-100.0,
        price_per_child=-50.0,
        extra_amount=-200.0,
        discount_amount=-50.0,
        vat_rate=-10.0,
    )
    assert res["adults_subtotal"] == 0.0
    assert res["children_subtotal"] == 0.0
    assert res["net_taxable"] == 0.0
    assert res["total_amount"] == 0.0


def test_backup_restore_functionality():
    # 1. Create a backup
    backup_zip = create_local_backup()
    assert backup_zip.exists()

    # 2. Add temporary quote to modify current DB
    temp_id = create_quote({
        "customer_first_name": "TestRestore",
        "customer_last_name": "Temporary",
        "event_type": "Compleanno",
        "guests_adults": 25,
        "price_per_adult": 80.0,
    })
    assert get_quote(temp_id) is not None

    # 3. Restore previous backup
    res = restore_from_backup_zip(backup_zip)
    assert res["restored"] is True

    # 4. Verify temporary quote is no longer present, DB restored accurately
    assert get_quote(temp_id) is None

    # 5. Check restore log entry
    restore_job = query_one("SELECT * FROM backup_jobs WHERE backup_type = 'restore' ORDER BY id DESC LIMIT 1")
    assert restore_job is not None
    assert restore_job["status"] == "restored"


def test_backup_restore_endpoints():
    client = TestClient(app)

    # 1. Test backup view shows restore panels
    res = client.get("/backup")
    assert res.status_code == 200
    assert "Ripristina Archivio da File" in res.text

    # 2. Test create backup via POST
    post_res = client.post("/backup", follow_redirects=False)
    assert post_res.status_code == 303
    assert "msg=backup_created" in post_res.headers["location"]

    # 3. Test restore from job id
    latest_job = query_one("SELECT id FROM backup_jobs WHERE backup_type = 'local' ORDER BY id DESC LIMIT 1")
    if latest_job:
        restore_res = client.post(f"/backup/restore/{latest_job['id']}", follow_redirects=False)
        assert restore_res.status_code == 303
        assert "msg=backup_restored" in restore_res.headers["location"]


