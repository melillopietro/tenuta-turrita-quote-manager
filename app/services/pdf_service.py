from __future__ import annotations

from pathlib import Path
from textwrap import wrap
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.graphics.shapes import Circle, Drawing, Ellipse, Rect, String
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.db import PDF_DIR, execute, settings_dict
from app.services.quote_service import get_quote, get_quote_contract, get_quote_items


def eur(value: float | int | None) -> str:
    value = float(value or 0)
    return f"€ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def safe(value: Any, fallback: str = "-") -> str:
    text = "" if value is None else str(value)
    return text if text.strip() else fallback


def paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(safe(text, "").replace("\n", "<br/>"), style)


def tenuta_logo_drawing() -> Drawing:
    drawing = Drawing(72, 72)
    green = colors.HexColor("#87977A")
    gold = colors.HexColor("#DDBA74")

    drawing.add(Rect(0, 0, 72, 72, fillColor=green, strokeColor=green))
    drawing.add(Ellipse(36, 36, 18, 28, fillColor=None, strokeColor=gold, strokeWidth=2))
    drawing.add(Ellipse(36, 36, 15, 25, fillColor=None, strokeColor=gold, strokeWidth=0.8))
    drawing.add(Circle(36, 17, 1.8, fillColor=gold, strokeColor=gold))
    drawing.add(Circle(36, 55, 1.8, fillColor=gold, strokeColor=gold))
    drawing.add(String(21, 27, "TT", fontName="Times-Roman", fontSize=23, fillColor=gold))

    return drawing


def build_pdf(quote_id: int) -> Path:
    quote = get_quote(quote_id)
    if quote is None:
        raise ValueError("Preventivo non trovato")

    items = get_quote_items(quote_id)
    contract = get_quote_contract(quote_id)
    settings = settings_dict()

    file_name = f"Preventivo_{quote['quote_number']}_{quote['event_type']}_{quote['last_name']}.pdf".replace(" ", "_")
    file_path = PDF_DIR / file_name

    doc = SimpleDocTemplate(
        str(file_path),
        pagesize=A4,
        rightMargin=1.6 * cm,
        leftMargin=1.6 * cm,
        topMargin=1.4 * cm,
        bottomMargin=1.4 * cm,
        title=f"Preventivo {quote['quote_number']}",
    )

    styles = getSampleStyleSheet()
    title = ParagraphStyle("TitleCustom", parent=styles["Title"], fontSize=20, leading=24, spaceAfter=12)
    h2 = ParagraphStyle("H2Custom", parent=styles["Heading2"], fontSize=13, leading=16, spaceBefore=8, spaceAfter=6)
    body = ParagraphStyle("BodyCustom", parent=styles["BodyText"], fontSize=9.5, leading=13)
    small = ParagraphStyle("SmallCustom", parent=styles["BodyText"], fontSize=8, leading=11, textColor=colors.HexColor("#444444"))

    story: list[Any] = []

    story.append(tenuta_logo_drawing())
    story.append(Spacer(1, 0.15 * cm))
    story.append(Paragraph(safe(settings.get("company_name"), "Tenuta Turrita"), title))
    payoff = settings.get("company_payoff")
    if payoff:
        story.append(Paragraph(payoff, small))

    company_line = " | ".join(
        x for x in [settings.get("company_address"), settings.get("company_phone"), settings.get("company_email")] if x
    )
    if company_line:
        story.append(Paragraph(company_line, small))
    story.append(Spacer(1, 0.25 * cm))
    story.append(Paragraph(f"Preventivo n. <b>{quote['quote_number']}</b>", h2))

    customer = f"{quote['first_name']} {quote['last_name']}".strip()
    secondary_customer = f"{quote['secondary_customer_first_name'] or ''} {quote['secondary_customer_last_name'] or ''}".strip()
    if secondary_customer:
        customer = f"{customer} e {secondary_customer}" if customer else secondary_customer

    event_name = quote['custom_event_type'] if quote['event_type'] == "Generico" and quote['custom_event_type'] else quote['event_type']

    info_table = Table(
        [
            ["Cliente", customer, "Email", safe(quote["email"])],
            ["Telefono", safe(quote["phone"]), "Evento", safe(event_name)],
            ["Data evento", safe(quote["event_date"]), "Orario", f"{safe(quote['event_start_time'])} - {safe(quote['event_end_time'])}"],
            ["Invitati adulti", safe(quote["guests_adults"]), "Bambini", safe(quote["guests_children"])],
            ["Location", safe(quote["location"]), "Compilato da", safe(quote["compiled_by_name"])],
        ],
        colWidths=[3.1 * cm, 5.4 * cm, 3.1 * cm, 5.4 * cm],
    )
    info_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7F3EB")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#DDDDDD")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("LEADING", (0, 0), (-1, -1), 10),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(info_table)
    story.append(Spacer(1, 0.35 * cm))

    story.append(Paragraph("Menù proposto", h2))
    if items:
        menu_rows = [["Portata", "Piatto", "Descrizione / Note"]]
        for item in items:
            course = item["custom_course_name"] if item["course_type"] == "Custom" and item["custom_course_name"] else item["course_type"]
            menu_group = item["menu_group"] if "menu_group" in item.keys() else "adult"
            if menu_group == "children":
                course = f"Menù bambini - {course}"
            detail = "<br/>".join(
                part for part in [safe(item["description"], ""), f"Allergeni: {item['allergens']}" if item["allergens"] else "", safe(item["notes"], "")] if part
            )
            menu_rows.append([paragraph(course, body), paragraph(item["dish_name"], body), paragraph(detail or "-", body)])
        menu_table = Table(menu_rows, colWidths=[4.0 * cm, 5.4 * cm, 7.6 * cm])
        menu_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EFE6D8")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#222222")),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#DDDDDD")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(menu_table)
    else:
        story.append(Paragraph("Nessun piatto inserito.", body))

    story.append(Spacer(1, 0.35 * cm))
    story.append(Paragraph("Riepilogo economico", h2))
    econ_table = Table(
        [
            ["Prezzo adulti", f"{quote['guests_adults']} x {eur(quote['price_per_adult'])}"],
            ["Prezzo bambini", f"{quote['guests_children']} x {eur(quote['price_per_child'])}"],
            ["Extra", eur(quote["extra_amount"])],
            ["Sconto", eur(quote["discount_amount"])],
            ["IVA", f"{quote['vat_rate']}%"],
            ["Totale preventivo", eur(quote["total_amount"])],
        ],
        colWidths=[7 * cm, 10 * cm],
    )
    econ_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#DDDDDD")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#F7F3EB")),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(econ_table)

    if quote["notes"]:
        story.append(Spacer(1, 0.25 * cm))
        story.append(Paragraph("Note", h2))
        story.append(paragraph(quote["notes"], body))

    contract_text = contract["contract_text"] if contract and contract["contract_text"] else settings.get("default_contract_terms", "")
    if contract_text:
        story.append(Spacer(1, 0.35 * cm))
        story.append(Paragraph("Condizioni contrattuali", h2))
        # Avoid oversized paragraphs by splitting around blank lines.
        for block in str(contract_text).split("\n\n"):
            if block.strip():
                story.append(paragraph(block.strip(), small))
                story.append(Spacer(1, 0.12 * cm))

    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("Firma cliente: ________________________________", body))
    story.append(Spacer(1, 0.18 * cm))
    story.append(Paragraph("Firma struttura: ______________________________", body))

    doc.build(story)
    execute("INSERT INTO quote_pdfs(quote_id, file_path) VALUES (?, ?)", (quote_id, str(file_path)))
    return file_path
