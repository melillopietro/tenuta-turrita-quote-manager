from __future__ import annotations

import smtplib
from email.message import EmailMessage
from pathlib import Path

from app.db import execute, settings_dict
from app.services.pdf_service import build_pdf, eur
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
    sender_name = settings.get("smtp_sender_name", "Tenuta Turrita").strip() or "Tenuta Turrita"
    company_name = settings.get("company_name", "Tenuta Turrita")
    company_phone = settings.get("company_phone", "+39 320 688 3788")
    company_address = settings.get("company_address", "Via Roma, Dragoni (CE)")
    secure = settings.get("smtp_secure", "false").lower() == "true"

    to_email = (recipient or quote["email"] or "").strip()
    if not host or not sender_email or not to_email:
        raise ValueError("Configurazione SMTP incompleta o indirizzo destinatario mancante")

    pdf_path = build_pdf(quote_id)
    event_name = quote["custom_event_type"] if quote["event_type"] == "Generico" and quote["custom_event_type"] else quote["event_type"]
    customer_name = f"{quote['first_name']} {quote['last_name']}".strip()
    event_date_str = quote["event_date"] or "Data da concordare"

    subject = f"Preventivo {company_name} - Rif. {quote['quote_number']} - {customer_name}"

    plain_body = custom_message or f"""Gentile {customer_name},

in allegato trasmettiamo la proposta di preventivo relativa all'evento {event_name} previsto per il giorno {event_date_str}.

Riepilogo Preventivo N. {quote['quote_number']}:
- Tipologia Evento: {event_name}
- Data Evento: {event_date_str}
- Numero Invitati: {quote['guests_adults']} adulti + {quote['guests_children']} bambini
- Importo Totale Complessivo: {eur(quote['total_amount'])}

Restiamo a Sua completa disposizione per qualsiasi personalizzazione o chiarimento.

Distinti saluti,
{sender_name}
{company_name}
Tel. {company_phone}
{company_address}
"""

    # Elegant HTML Email Template matching Tenuta Turrita theme
    html_paragraphs = "".join(f"<p style='margin: 0 0 12px 0; font-size: 14.5px; line-height: 1.6; color: #2F352C;'>{p.strip()}</p>" for p in plain_body.split("\n\n") if p.strip())

    html_body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #F6F3EC; margin: 0; padding: 24px; color: #2F352C; }}
    .container {{ max-width: 600px; margin: 0 auto; background-color: #FFFFFF; border-radius: 12px; overflow: hidden; border: 1px solid #D9D5CA; box-shadow: 0 8px 24px rgba(0,0,0,0.06); }}
    .header {{ background-color: #87977A; padding: 26px 30px; text-align: center; border-bottom: 3px solid #DDBA74; }}
    .header h1 {{ margin: 0; color: #FFFFFF; font-size: 24px; font-family: Georgia, serif; font-weight: normal; letter-spacing: 0.5px; }}
    .header p {{ margin: 4px 0 0 0; color: #F7F3EB; font-size: 12.5px; font-style: italic; }}
    .content {{ padding: 32px 30px; }}
    .recap-box {{ background-color: #F7F3EB; border: 1px solid #E8E2D5; border-radius: 8px; padding: 18px 20px; margin: 22px 0; }}
    .recap-title {{ font-size: 13px; font-weight: bold; text-transform: uppercase; letter-spacing: 0.08em; color: #6F8062; margin-bottom: 10px; }}
    .recap-table {{ width: 100%; border-collapse: collapse; font-size: 13.5px; }}
    .recap-table td {{ padding: 5px 0; vertical-align: top; }}
    .recap-table td.label {{ color: #6C7367; width: 40%; font-weight: 600; }}
    .recap-table td.value {{ color: #2F352C; font-weight: bold; }}
    .recap-total {{ border-top: 1px solid #D9D5CA; margin-top: 8px; padding-top: 8px; font-size: 15px; color: #87977A; font-weight: bold; }}
    .footer {{ background-color: #FAF8F5; padding: 20px 30px; text-align: center; border-top: 1px solid #EAE6DD; font-size: 12px; color: #888888; line-height: 1.5; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>{company_name}</h1>
      <p>Villa per matrimoni ed eventi</p>
    </div>
    <div class="content">
      {html_paragraphs}

      <div class="recap-box">
        <div class="recap-title">Riepilogo Proposta Economica</div>
        <table class="recap-table">
          <tr><td class="label">Numero Preventivo:</td><td class="value">{quote['quote_number']}</td></tr>
          <tr><td class="label">Tipologia Evento:</td><td class="value">{event_name}</td></tr>
          <tr><td class="label">Data Evento:</td><td class="value">{event_date_str}</td></tr>
          <tr><td class="label">Numero Ospiti:</td><td class="value">{quote['guests_adults']} adulti + {quote['guests_children']} bambini</td></tr>
          <tr><td class="label">Totale Complessivo:</td><td class="value" style="color: #6F8062; font-size: 15px;">{eur(quote['total_amount'])}</td></tr>
        </table>
      </div>

      <p style="font-size: 13px; color: #6C7367; margin-top: 24px;">
        In allegato alla presente è disponibile il documento PDF ufficiale dettagliato con menù completo e prospetto economico.
      </p>
    </div>
    <div class="footer">
      <strong>{company_name}</strong><br>
      {company_address} · Tel. {company_phone}<br>
      Documento generato dal Gestionale Ufficiale Tenuta Turrita
    </div>
  </div>
</body>
</html>
"""

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{sender_name} <{sender_email}>"
    msg["To"] = to_email
    msg.set_content(plain_body)
    msg.add_alternative(html_body, subtype="html")

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
