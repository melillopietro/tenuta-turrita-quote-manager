from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.db import BACKUP_DIR, init_db, query_all, query_one, set_setting, settings_dict
from app.services.backup_service import create_backup_with_optional_drive
from app.services.email_service import send_quote_email
from app.services.pdf_service import build_pdf, eur
from app.services.quote_service import (
    COURSE_TYPES,
    EVENT_TYPES,
    MENU_PRESETS,
    STATUSES,
    calculate_quote_breakdown,
    create_quote,
    dashboard_stats,
    default_contract_template,
    delete_quote,
    duplicate_quote,
    get_quote,
    get_quote_contract,
    get_quote_items,
    list_quotes,
    update_quote,
    update_quote_status,
    upsert_contract,
)

from contextlib import asynccontextmanager
from app.paths import STATIC_DIR, TEMPLATES_DIR


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Tenuta Turrita Quote Manager", version="0.2.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
templates.env.filters["eur"] = eur


def redirect(path: str) -> RedirectResponse:
    return RedirectResponse(path, status_code=303)


async def form_to_dict(request: Request) -> dict[str, Any]:
    form = await request.form()
    data: dict[str, Any] = {}
    for key in form.keys():
        values = form.getlist(key)
        data[key] = values if len(values) > 1 else values[0]
    # Force list fields, because one item still needs to be treated as list.
    for key in ["menu_group", "course_type", "custom_course_name", "dish_name", "description", "allergens", "item_notes", "extra_price"]:
        data[key] = form.getlist(key)
    return data


@app.get("/api/presets/{preset_key}")
def get_preset_api(preset_key: str) -> dict[str, Any]:
    preset = MENU_PRESETS.get(preset_key)
    if not preset:
        return {"error": "Preset non trovato"}
    return preset


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    stats = dashboard_stats()
    recent = list_quotes()[:6]
    return templates.TemplateResponse("dashboard.html", {"request": request, "stats": stats, "recent": recent})


@app.get("/quotes", response_class=HTMLResponse)
def quotes(
    request: Request,
    q: str | None = None,
    status: str | None = None,
    event_type: str | None = None,
    year: str | None = None,
    sort_by: str | None = "created_desc",
    msg: str | None = None,
) -> HTMLResponse:
    quotes_list = list_quotes(q=q, status=status, event_type=event_type, year=year, sort_by=sort_by)
    stats = dashboard_stats()

    # Get available distinct years for dropdown
    years_rows = query_all("SELECT DISTINCT year FROM quotes ORDER BY year DESC")
    available_years = [r["year"] for r in years_rows]

    return templates.TemplateResponse(
        "quotes.html",
        {
            "request": request,
            "quotes": quotes_list,
            "statuses": STATUSES,
            "event_types": EVENT_TYPES,
            "available_years": available_years,
            "current_q": q or "",
            "current_status": status or "all",
            "current_event_type": event_type or "all",
            "current_year": year or "all",
            "current_sort": sort_by or "created_desc",
            "stats": stats,
            "msg": msg,
        },
    )


@app.get("/quotes/new", response_class=HTMLResponse)
def new_quote(request: Request) -> HTMLResponse:
    staff = query_all("SELECT * FROM staff WHERE active = 1 ORDER BY name")
    settings = settings_dict()
    return templates.TemplateResponse(
        "quote_form.html",
        {
            "request": request,
            "event_types": EVENT_TYPES,
            "course_types": COURSE_TYPES,
            "menu_presets": MENU_PRESETS,
            "staff": staff,
            "settings": settings,
        },
    )


@app.post("/quotes/new")
async def create_quote_route(request: Request) -> RedirectResponse:
    data = await form_to_dict(request)
    quote_id = create_quote(data)
    return redirect(f"/quotes/{quote_id}?msg=created")


@app.get("/quotes/{quote_id}", response_class=HTMLResponse)
def quote_detail(request: Request, quote_id: int, msg: str | None = None) -> HTMLResponse:
    quote = get_quote(quote_id)
    if quote is None:
        return templates.TemplateResponse("error.html", {"request": request, "message": "Preventivo non trovato"}, status_code=404)
    items = get_quote_items(quote_id)
    contract = get_quote_contract(quote_id)
    email_logs = query_all("SELECT * FROM email_logs WHERE quote_id = ? ORDER BY sent_at DESC", (quote_id,))
    pdfs = query_all("SELECT * FROM quote_pdfs WHERE quote_id = ? ORDER BY generated_at DESC", (quote_id,))
    breakdown = calculate_quote_breakdown(
        guests_adults=quote["guests_adults"],
        guests_children=quote["guests_children"],
        price_per_adult=quote["price_per_adult"],
        price_per_child=quote["price_per_child"],
        extra_amount=quote["extra_amount"],
        discount_amount=quote["discount_amount"],
        vat_rate=quote["vat_rate"],
    )
    return templates.TemplateResponse(
        "quote_detail.html",
        {
            "request": request,
            "quote": quote,
            "items": items,
            "contract": contract,
            "email_logs": email_logs,
            "pdfs": pdfs,
            "statuses": STATUSES,
            "breakdown": breakdown,
            "msg": msg,
        },
    )


@app.get("/quotes/{quote_id}/edit", response_class=HTMLResponse)
def edit_quote_form(request: Request, quote_id: int) -> HTMLResponse:
    quote = get_quote(quote_id)
    if quote is None:
        return templates.TemplateResponse("error.html", {"request": request, "message": "Preventivo non trovato"}, status_code=404)

    staff = query_all("SELECT * FROM staff WHERE active = 1 ORDER BY name")
    items = get_quote_items(quote_id)

    return templates.TemplateResponse(
        "quote_edit.html",
        {
            "request": request,
            "quote": quote,
            "items": items,
            "event_types": EVENT_TYPES,
            "course_types": COURSE_TYPES,
            "menu_presets": MENU_PRESETS,
            "staff": staff,
            "settings": settings_dict(),
        },
    )


@app.post("/quotes/{quote_id}/edit")
async def update_quote_route(request: Request, quote_id: int) -> RedirectResponse:
    data = await form_to_dict(request)
    update_quote(quote_id, data)
    return redirect(f"/quotes/{quote_id}?msg=updated")


@app.post("/quotes/{quote_id}/delete")
async def delete_quote_route(quote_id: int) -> RedirectResponse:
    delete_quote(quote_id)
    return redirect("/quotes?msg=deleted")


@app.post("/quotes/{quote_id}/duplicate")
async def duplicate_quote_route(quote_id: int) -> RedirectResponse:
    new_quote_id = duplicate_quote(quote_id)
    return redirect(f"/quotes/{new_quote_id}?msg=duplicated")


@app.post("/quotes/{quote_id}/status")
async def quote_status(quote_id: int, status: str = Form(...)) -> RedirectResponse:
    update_quote_status(quote_id, status)
    return redirect(f"/quotes/{quote_id}?msg=status_updated")


@app.get("/quotes/{quote_id}/pdf")
def quote_pdf(quote_id: int) -> FileResponse:
    pdf_path = build_pdf(quote_id)
    return FileResponse(str(pdf_path), media_type="application/pdf", filename=pdf_path.name)


@app.get("/quotes/{quote_id}/print", response_class=HTMLResponse)
def quote_print(request: Request, quote_id: int) -> HTMLResponse:
    quote = get_quote(quote_id)
    if quote is None:
        return templates.TemplateResponse("error.html", {"request": request, "message": "Preventivo non trovato"}, status_code=404)
    breakdown = calculate_quote_breakdown(
        guests_adults=quote["guests_adults"],
        guests_children=quote["guests_children"],
        price_per_adult=quote["price_per_adult"],
        price_per_child=quote["price_per_child"],
        extra_amount=quote["extra_amount"],
        discount_amount=quote["discount_amount"],
        vat_rate=quote["vat_rate"],
    )
    return templates.TemplateResponse(
        "quote_print.html",
        {
            "request": request,
            "quote": quote,
            "items": get_quote_items(quote_id),
            "contract": get_quote_contract(quote_id),
            "settings": settings_dict(),
            "breakdown": breakdown,
        },
    )


@app.get("/quotes/{quote_id}/contract", response_class=HTMLResponse)
def contract_form(request: Request, quote_id: int) -> HTMLResponse:
    quote = get_quote(quote_id)
    if quote is None:
        return templates.TemplateResponse("error.html", {"request": request, "message": "Preventivo non trovato"}, status_code=404)
    contract = get_quote_contract(quote_id)
    settings = settings_dict()
    template_text = contract["contract_text"] if contract else default_contract_template(
        {
            "quote_expiry_date": "[DATA_SCADENZA_PREVENTIVO]",
            "deposit_amount": "[IMPORTO_CAPARRA]",
            "account_holder": settings.get("company_account_holder", "[INTESTATARIO_CONTO]"),
            "iban": settings.get("company_iban", "[IBAN]"),
            "event_type": quote["custom_event_type"] if quote["event_type"] == "Generico" and quote["custom_event_type"] else quote["event_type"],
            "event_date": quote["event_date"],
            "customer_name": f"{quote['first_name']} {quote['last_name']}",
            "balance_due_date": "[DATA_SALDO]",
            "guest_confirmation_date": "[DATA_CONFERMA_INVITATI]",
            "cancellation_deadline": "[DATA_LIMITE_ANNULLAMENTO]",
        }
    )
    return templates.TemplateResponse(
        "contract_form.html",
        {
            "request": request,
            "quote": quote,
            "contract": contract,
            "settings": settings,
            "template_text": template_text,
        },
    )


@app.post("/quotes/{quote_id}/contract")
async def save_contract(request: Request, quote_id: int) -> RedirectResponse:
    data = await form_to_dict(request)
    upsert_contract(quote_id, data)
    return redirect(f"/quotes/{quote_id}?msg=contract_saved")


@app.get("/quotes/{quote_id}/send", response_class=HTMLResponse)
def send_form(request: Request, quote_id: int) -> HTMLResponse:
    quote = get_quote(quote_id)
    if quote is None:
        return templates.TemplateResponse("error.html", {"request": request, "message": "Preventivo non trovato"}, status_code=404)
    settings = settings_dict()
    event_name = quote["custom_event_type"] if quote["event_type"] == "Generico" and quote["custom_event_type"] else quote["event_type"]
    message = f"""Gentile {quote['first_name']} {quote['last_name']},

in allegato trasmettiamo il preventivo relativo all'evento {event_name} previsto per il giorno {quote['event_date']}.

Restiamo a disposizione per qualsiasi chiarimento o richiesta di personalizzazione.

Cordiali saluti,
{settings.get('smtp_sender_name') or settings.get('company_name') or 'Tenuta Turrita'}
"""
    return templates.TemplateResponse(
        "send_form.html",
        {"request": request, "quote": quote, "settings": settings, "message": message},
    )


@app.post("/quotes/{quote_id}/send", response_model=None)
async def send_quote(request: Request, quote_id: int):
    data = await form_to_dict(request)
    try:
        send_quote_email(quote_id, recipient=data.get("recipient"), custom_message=data.get("message"))
        return redirect(f"/quotes/{quote_id}?msg=email_sent")
    except Exception as exc:
        quote = get_quote(quote_id)
        return templates.TemplateResponse(
            "send_form.html",
            {"request": request, "quote": quote, "settings": settings_dict(), "message": data.get("message", ""), "error": str(exc)},
            status_code=400,
        )


@app.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request, msg: str | None = None) -> HTMLResponse:
    staff = query_all("SELECT * FROM staff ORDER BY active DESC, name")
    return templates.TemplateResponse("settings.html", {"request": request, "settings": settings_dict(), "staff": staff, "msg": msg})


@app.post("/settings")
async def save_settings(request: Request) -> RedirectResponse:
    data = await form_to_dict(request)
    allowed = [
        "company_name", "company_address", "company_phone", "company_email", "company_iban", "company_account_holder", "company_payoff",
        "smtp_host", "smtp_port", "smtp_secure", "smtp_username", "smtp_password", "smtp_sender_name", "smtp_sender_email",
        "drive_backup_enabled",
    ]
    for key in allowed:
        value = data.get(key, "")
        if key in ["smtp_secure", "drive_backup_enabled"]:
            value = "true" if data.get(key) == "on" else "false"
        set_setting(key, str(value))
    return redirect("/settings?msg=settings_saved")


@app.post("/settings/staff")
async def add_staff(request: Request) -> RedirectResponse:
    data = await form_to_dict(request)
    from app.db import execute
    if data.get("staff_name"):
        execute(
            "INSERT INTO staff(name, role, email) VALUES (?, ?, ?)",
            (data.get("staff_name", "").strip(), data.get("staff_role", "").strip(), data.get("staff_email", "").strip()),
        )
    return redirect("/settings?msg=staff_added")


@app.get("/backup", response_class=HTMLResponse)
def backup_page(request: Request, msg: str | None = None) -> HTMLResponse:
    jobs = query_all("SELECT * FROM backup_jobs ORDER BY created_at DESC LIMIT 20")
    return templates.TemplateResponse("backup.html", {"request": request, "jobs": jobs, "settings": settings_dict(), "msg": msg})


@app.post("/backup")
def create_backup() -> RedirectResponse:
    create_backup_with_optional_drive()
    return redirect("/backup?msg=backup_created")


@app.get("/backup/download/{job_id}")
def download_backup(job_id: int) -> FileResponse:
    job = query_one("SELECT * FROM backup_jobs WHERE id = ?", (job_id,))
    if job is None:
        raise ValueError("Backup non trovato")
    path = Path(job["file_path"])
    return FileResponse(str(path), media_type="application/zip", filename=path.name)
