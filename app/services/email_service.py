from __future__ import annotations

import smtplib
from email.message import EmailMessage
from pathlib import Path

from app.db import execute, settings_dict
from app.services.pdf_service import build_pdf
from app.services.quote_service import get_quote, update_quote_status


def send_quote_email(quote_id: int, recipient: str | None = None, custom_message: str | None = None) -> None:
    settings = settings_dict()
    quote = get_quote(quote_id)
    if quote is None:
        raise ValueError("Preventivo non trovato")

    host = settings.get("smtp_host", "").strip()
    port = int(settings.get("smtp_port", "587") or 587)
    username = settings.get("smtp_username", "").strip()
    password = settings.get("smtp_password", "")
    sender_email = settings.get("smtp_sender_email", "").strip() or username
    sender_name = settings.get("smtp_sender_name", "Ristorante").strip() or "Ristorante"
    secure = settings.get("smtp_secure", "false").lower() == "true"

    to_email = recipient or quote["email"]
    if not host or not sender_email or not to_email:
        raise ValueError("Configurazione SMTP incompleta o destinatario mancante")

    pdf_path = build_pdf(quote_id)
    event_name = quote["custom_event_type"] if quote["event_type"] == "Generico" and quote["custom_event_type"] else quote["event_type"]

    subject = f"Preventivo evento {event_name} - {quote['event_date']} - {quote['quote_number']}"
    body = custom_message or f"""Gentile {quote['first_name']} {quote['last_name']},

in allegato trasmettiamo il preventivo relativo all'evento {event_name} previsto per il giorno {quote['event_date']}.

Restiamo a disposizione per eventuali modifiche o chiarimenti.

Cordiali saluti,
{sender_name}
"""

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{sender_name} <{sender_email}>"
    msg["To"] = to_email
    msg.set_content(body)

    path = Path(pdf_path)
    msg.add_attachment(path.read_bytes(), maintype="application", subtype="pdf", filename=path.name)

    try:
        if secure:
            with smtplib.SMTP_SSL(host, port, timeout=20) as smtp:
                if username:
                    smtp.login(username, password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=20) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.ehlo()
                if username:
                    smtp.login(username, password)
                smtp.send_message(msg)
        execute(
            "INSERT INTO email_logs(quote_id, recipient_email, subject, status) VALUES (?, ?, ?, ?)",
            (quote_id, to_email, subject, "sent"),
        )
        update_quote_status(quote_id, "inviato")
    except Exception as exc:
        execute(
            "INSERT INTO email_logs(quote_id, recipient_email, subject, status, error_message) VALUES (?, ?, ?, ?, ?)",
            (quote_id, to_email, subject, "failed", str(exc)),
        )
        raise
