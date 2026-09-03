from __future__ import annotations

from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.db import execute, settings_dict
from app.paths import LOGO_PATH, PDF_DIR
from app.services.quote_service import (
    calculate_quote_breakdown,
    get_quote,
    get_quote_contract,
    get_quote_items,
)


import html


def eur(value: float | int | None) -> str:
    value = float(value or 0)
    return f"€ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def safe(value: Any, fallback: str = "-") -> str:
    text = "" if value is None else str(value)
    return text if text.strip() else fallback


def paragraph(text: str, style: ParagraphStyle, is_html: bool = False) -> Paragraph:
    val = safe(text, "")
    if not is_html:
        val = html.escape(val, quote=False)
    return Paragraph(val.replace("\n", "<br/>"), style)


class NumberedCanvas(canvas.Canvas):
    """Canvas a due passate per calcolare il numero totale di pagine e disegnare header/footer coerenti."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._saved_page_states: list[dict[str, Any]] = []
        self.doc_quote_number: str = ""

    def showPage(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int) -> None:
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#6C7367"))

        # Header per pagine successive alla prima
        if self._pageNumber > 1:
            self.setStrokeColor(colors.HexColor("#DDBA74"))
            self.setLineWidth(0.75)
            self.line(1.6 * cm, 28.3 * cm, 19.4 * cm, 28.3 * cm)
            self.drawString(1.6 * cm, 28.5 * cm, "Tenuta Turrita · Villa per matrimoni ed eventi")
            if self.doc_quote_number:
                self.drawRightString(19.4 * cm, 28.5 * cm, f"Preventivo {self.doc_quote_number}")

        # Footer elegante su tutte le pagine
        self.setStrokeColor(colors.HexColor("#DDBA74"))
        self.setLineWidth(0.75)
        self.line(1.6 * cm, 1.6 * cm, 19.4 * cm, 1.6 * cm)
        self.drawString(1.6 * cm, 1.15 * cm, "Tenuta Turrita · Via Roma, Dragoni (CE) · Tel. +39 320 688 3788")
        self.drawRightString(19.4 * cm, 1.15 * cm, f"Pagina {self._pageNumber} di {page_count}")
        self.restoreState()


def build_pdf(quote_id: int) -> Path:
    raw_quote = get_quote(quote_id)
    if raw_quote is None:
        raise ValueError("Preventivo non trovato")

    quote = dict(raw_quote)
    items = [dict(it) for it in get_quote_items(quote_id)]
    contract = dict(get_quote_contract(quote_id)) if get_quote_contract(quote_id) else {}
    settings = settings_dict()

    import re
    clean_last_name = re.sub(r'[<>:"/\\|?*]', '', quote['last_name']).strip()
    file_name = f"Preventivo_{quote['quote_number']}_{quote['event_type']}_{clean_last_name}.pdf".replace(" ", "_")
    file_path = PDF_DIR / file_name

    doc = SimpleDocTemplate(
        str(file_path),
        pagesize=A4,
        rightMargin=1.6 * cm,
        leftMargin=1.6 * cm,
        topMargin=1.5 * cm,
        bottomMargin=2.0 * cm,
        title=f"Preventivo {quote['quote_number']} - Tenuta Turrita",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleCustom", parent=styles["Title"], fontSize=18, leading=22, textColor=colors.HexColor("#2F352C"), spaceAfter=2)
    payoff_style = ParagraphStyle("PayoffCustom", parent=styles["BodyText"], fontSize=9, leading=12, textColor=colors.HexColor("#6F8062"), fontName="Helvetica-Oblique")
    company_meta_style = ParagraphStyle("CompanyMeta", parent=styles["BodyText"], fontSize=8, leading=11, textColor=colors.HexColor("#6C7367"))
    h2 = ParagraphStyle("H2Custom", parent=styles["Heading2"], fontSize=12, leading=15, textColor=colors.HexColor("#2F352C"), spaceBefore=10, spaceAfter=5)
    body = ParagraphStyle("BodyCustom", parent=styles["BodyText"], fontSize=9, leading=12, textColor=colors.HexColor("#2F352C"))
    small = ParagraphStyle("SmallCustom", parent=styles["BodyText"], fontSize=8, leading=11, textColor=colors.HexColor("#444444"))
    badge_style = ParagraphStyle("BadgeStyle", parent=styles["BodyText"], fontSize=8, leading=10, fontName="Helvetica-Bold", textColor=colors.HexColor("#6F8062"))

    story: list[Any] = []

    # Intestazione con Logo Ufficiale e Dati Struttura
    header_data: list[list[Any]] = []
    logo_cell: Any = ""
    if LOGO_PATH.exists():
        logo_cell = Image(str(LOGO_PATH), width=2.4 * cm, height=2.4 * cm)

    brand_text = [
        Paragraph(f"<b>{safe(settings.get('company_name'), 'Tenuta Turrita')}</b>", title_style),
        Paragraph(safe(settings.get("company_payoff"), "Villa per matrimoni ed eventi"), payoff_style),
        Spacer(1, 0.1 * cm),
        Paragraph(" · ".join(x for x in [settings.get("company_address"), settings.get("company_phone"), settings.get("company_email")] if x), company_meta_style),
    ]

    header_table = Table([[logo_cell, brand_text]], colWidths=[2.7 * cm, 15.1 * cm])
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(header_table)

    # Linea decorativa dorata
    sep_table = Table([[""]], colWidths=[17.8 * cm], rowHeights=[2])
    sep_table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#DDBA74")), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
    story.append(sep_table)
    story.append(Spacer(1, 0.25 * cm))

    # Titolo Preventivo e Data emissione
    story.append(Paragraph(f"PREVENTIVO N. <b>{quote['quote_number']}</b>", h2))

    # Dati Cliente ed Evento
    customer = f"{quote['first_name']} {quote['last_name']}".strip()
    if quote.get("primary_customer_role"):
        customer = f"{quote['primary_customer_role']}: {customer}"

    secondary_customer = f"{quote.get('secondary_customer_first_name') or ''} {quote.get('secondary_customer_last_name') or ''}".strip()
    if secondary_customer:
        sec_role = f"{quote.get('secondary_customer_role')}: " if quote.get("secondary_customer_role") else ""
        customer = f"{customer} & {sec_role}{secondary_customer}"

    event_name = quote["custom_event_type"] if quote["event_type"] == "Generico" and quote["custom_event_type"] else quote["event_type"]

    info_table = Table(
        [
            ["Intestatario/i", customer, "Email", safe(quote["email"])],
            ["Recapito tel.", safe(quote["phone"]), "Tipologia Evento", safe(event_name)],
            ["Data Evento", safe(quote["event_date"]), "Orario concordato", f"{safe(quote['event_start_time'])} - {safe(quote['event_end_time'])}"],
            ["Numero Invitati", f"{safe(quote['guests_adults'])} adulti + {safe(quote['guests_children'])} bambini", "Location", safe(quote["location"])],
            ["Compilato da", safe(quote.get("compiled_by_name")), "Data preventivo", quote.get("created_at", "")[:10] if quote.get("created_at") else "-"],
        ],
        colWidths=[3.2 * cm, 5.7 * cm, 3.2 * cm, 5.7 * cm],
    )
    info_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7F3EB")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D9D5CA")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#2F352C")),
                ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#2F352C")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("LEADING", (0, 0), (-1, -1), 11),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(info_table)
    story.append(Spacer(1, 0.3 * cm))

    # Proposta Gastronomica / Menù
    story.append(Paragraph("PROPOSTA GASTRONOMICA & MENÙ", h2))
    if items:
        menu_rows = [["Menù / Portata", "Piatto Selezionato", "Descrizione, Ingredienti & Allergeni"]]
        for item in items:
            course = item["custom_course_name"] if item["course_type"] == "Custom" and item["custom_course_name"] else item["course_type"]
            menu_group = item["menu_group"] if "menu_group" in item.keys() else "adult"
            group_label = "Menù Adulti" if menu_group != "children" else "Menù Bambini"
            course_cell = f"<b>{html.escape(group_label)}</b><br/>{html.escape(str(course))}"

            detail_parts = []
            if item["description"]:
                detail_parts.append(html.escape(str(item["description"])))
            if item["allergens"]:
                detail_parts.append(f"<font color='#6F8062'><b>Allergeni:</b> {html.escape(str(item['allergens']))}</font>")
            if item["notes"]:
                detail_parts.append(f"<i>Note: {html.escape(str(item['notes']))}</i>")
            detail_text = "<br/>".join(part for part in detail_parts if part)

            dish_clean = html.escape(str(item["dish_name"]))
            dish_text = f"<b>{dish_clean}</b>"
            if item.get("is_extra") and float(item.get("extra_price", 0)) > 0:
                dish_text += f"<br/><font color='#6F8062'>+ {eur(item['extra_price'])} a persona</font>"

            menu_rows.append([paragraph(course_cell, badge_style, is_html=True), paragraph(dish_text, body, is_html=True), paragraph(detail_text or "-", body, is_html=True)])

        menu_table = Table(menu_rows, colWidths=[4.2 * cm, 5.6 * cm, 8.0 * cm])
        menu_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EFE9DD")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#2F352C")),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D9D5CA")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(menu_table)
    else:
        story.append(Paragraph("Nessun piatto inserito.", body))

    story.append(Spacer(1, 0.35 * cm))

    # Blocco Riepilogo Economico + Firme con KeepTogether
    closing_elements: list[Any] = []

    closing_elements.append(Paragraph("PROSPETTO ECONOMICO", h2))
    breakdown = calculate_quote_breakdown(
        guests_adults=quote["guests_adults"],
        guests_children=quote["guests_children"],
        price_per_adult=quote["price_per_adult"],
        price_per_child=quote["price_per_child"],
        extra_amount=quote["extra_amount"],
        discount_amount=quote["discount_amount"],
        vat_rate=quote["vat_rate"],
    )

    econ_rows = [
        ["Quota Ospiti Adulti", f"{quote['guests_adults']} ospiti × {eur(quote['price_per_adult'])}", eur(breakdown['adults_subtotal'])],
        ["Quota Bambini", f"{quote['guests_children']} ospiti × {eur(quote['price_per_child'])}", eur(breakdown['children_subtotal'])],
    ]
    if breakdown["extra_amount"] > 0:
        econ_rows.append(["Servizi & Dotazioni Extra", "Servizi personalizzati", eur(breakdown["extra_amount"])])
    if breakdown["discount_amount"] > 0:
        econ_rows.append(["Sconto Riservato", "Agevolazione concordata", f"- {eur(breakdown['discount_amount'])}"])

    econ_rows.extend(
        [
            ["Totale Imponibile Netto", "", eur(breakdown["net_taxable"])],
            [f"Imposta IVA ({quote['vat_rate']}%)", f"Aliquota applicata {quote['vat_rate']}%", eur(breakdown["vat_amount"])],
            ["TOTALE COMPLESSIVO PREVENTIVO", "", eur(breakdown["total_amount"])],
        ]
    )

    econ_table = Table(econ_rows, colWidths=[6.5 * cm, 6.5 * cm, 4.8 * cm])
    econ_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D9D5CA")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica"),
                ("FONTNAME", (0, -3), (-1, -3), "Helvetica-Bold"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("ALIGN", (2, 0), (2, -1), "RIGHT"),
                ("BACKGROUND", (0, -3), (-1, -3), colors.HexColor("#F7F3EB")),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#87977A")),
                ("TEXTCOLOR", (0, -1), (-1, -1), colors.HexColor("#FFFFFF")),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("FONTSIZE", (0, -1), (-1, -1), 10),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    closing_elements.append(econ_table)

    if quote["notes"]:
        closing_elements.append(Spacer(1, 0.2 * cm))
        closing_elements.append(Paragraph("NOTE & ACCORDI PARTICOLARI", h2))
        closing_elements.append(paragraph(quote["notes"], body))

    contract_text = contract.get("contract_text") if contract and contract.get("contract_text") else settings.get("default_contract_terms", "")
    if contract_text:
        closing_elements.append(Spacer(1, 0.25 * cm))
        closing_elements.append(Paragraph("CONDIZIONI GENERALI DI CONFERMA", h2))
        for block in str(contract_text).split("\n\n"):
            if block.strip():
                closing_elements.append(paragraph(block.strip(), small))
                closing_elements.append(Spacer(1, 0.1 * cm))

    closing_elements.append(Spacer(1, 0.35 * cm))
    sig_table = Table(
        [
            ["Data e Luogo: ________________________", "Per Accettazione il Cliente: ________________________"],
            ["", "Per la Direzione Tenuta Turrita: ___________________"],
        ],
        colWidths=[8.9 * cm, 8.9 * cm],
    )
    sig_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    closing_elements.append(sig_table)

    story.append(KeepTogether(closing_elements))

    # Costruzione del PDF con NumberedCanvas
    def make_canvas(*args: Any, **kwargs: Any) -> NumberedCanvas:
        c = NumberedCanvas(*args, **kwargs)
        c.doc_quote_number = quote["quote_number"]
        return c

    doc.build(story, canvasmaker=make_canvas)
    execute("INSERT INTO quote_pdfs(quote_id, file_path) VALUES (?, ?)", (quote_id, str(file_path)))
    return file_path
