from __future__ import annotations

from datetime import datetime
from typing import Any

from app.db import get_connection, query_all, query_one

EVENT_TYPES = ["Matrimonio", "Cresima", "Battesimo", "Compleanno", "Laurea", "Generico"]
COURSE_TYPES = [
    "Buffet di benvenuto",
    "Aperitivo",
    "Antipasto",
    "Primo",
    "Secondo",
    "Frutta",
    "Dolci",
    "Custom",
]
STATUSES = ["bozza", "inviato", "in_attesa", "accettato", "rifiutato", "scaduto", "annullato"]


def money(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        return 0.0


def integer(value: Any) -> int:
    if value in (None, ""):
        return 0
    try:
        return int(value)
    except ValueError:
        return 0


def calculate_total(
    guests_adults: int,
    guests_children: int,
    price_per_adult: float,
    price_per_child: float,
    extra_amount: float,
    discount_amount: float,
    vat_rate: float,
) -> float:
    subtotal = (guests_adults * price_per_adult) + (guests_children * price_per_child) + extra_amount - discount_amount
    subtotal = max(subtotal, 0)
    total = subtotal + (subtotal * vat_rate / 100)
    return round(total, 2)


def next_quote_number() -> tuple[str, int, int]:
    year = datetime.now().year
    with get_connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT last_number FROM quote_counters WHERE year = ?", (year,)).fetchone()
        if row is None:
            progressive = 1
            conn.execute("INSERT INTO quote_counters(year, last_number) VALUES (?, ?)", (year, progressive))
        else:
            progressive = int(row["last_number"]) + 1
            conn.execute("UPDATE quote_counters SET last_number = ? WHERE year = ?", (progressive, year))
        conn.commit()
    return f"{year}-{progressive:04d}", year, progressive


def create_quote(form: dict[str, Any]) -> int:
    quote_number, year, progressive = next_quote_number()

    guests_adults = integer(form.get("guests_adults"))
    guests_children = integer(form.get("guests_children"))
    price_per_adult = money(form.get("price_per_adult"))
    price_per_child = money(form.get("price_per_child"))
    extra_amount = money(form.get("extra_amount"))
    discount_amount = money(form.get("discount_amount"))
    vat_rate = money(form.get("vat_rate"))
    total_amount = calculate_total(
        guests_adults,
        guests_children,
        price_per_adult,
        price_per_child,
        extra_amount,
        discount_amount,
        vat_rate,
    )

    with get_connection() as conn:
        customer_id = conn.execute(
            """
            INSERT INTO customers(first_name, last_name, phone, email, address, fiscal_code, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                form.get("customer_first_name", "").strip(),
                form.get("customer_last_name", "").strip(),
                form.get("customer_phone", "").strip(),
                form.get("customer_email", "").strip(),
                form.get("customer_address", "").strip(),
                form.get("customer_fiscal_code", "").strip(),
                form.get("customer_notes", "").strip(),
            ),
        ).lastrowid

        quote_id = conn.execute(
            """
            INSERT INTO quotes(
                quote_number, year, progressive_number, customer_id, event_type, custom_event_type,
                event_date, event_start_time, event_end_time, guests_adults, guests_children,
                location, status, compiled_by_staff_id, price_per_adult, price_per_child,
                extra_amount, discount_amount, vat_rate, total_amount, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                quote_number,
                year,
                progressive,
                customer_id,
                form.get("event_type", "Generico"),
                form.get("custom_event_type", "").strip(),
                form.get("event_date", ""),
                form.get("event_start_time", ""),
                form.get("event_end_time", ""),
                guests_adults,
                guests_children,
                form.get("location", "").strip(),
                "bozza",
                integer(form.get("compiled_by_staff_id")) or None,
                price_per_adult,
                price_per_child,
                extra_amount,
                discount_amount,
                vat_rate,
                total_amount,
                form.get("notes", "").strip(),
            ),
        ).lastrowid

        conn.execute(
            """
            UPDATE quotes
            SET primary_customer_role = ?,
                secondary_customer_role = ?,
                secondary_customer_first_name = ?,
                secondary_customer_last_name = ?,
                secondary_customer_phone = ?,
                secondary_customer_email = ?
            WHERE id = ?
            """,
            (
                form.get("primary_customer_role", "").strip(),
                form.get("secondary_customer_role", "").strip(),
                form.get("secondary_customer_first_name", "").strip(),
                form.get("secondary_customer_last_name", "").strip(),
                form.get("secondary_customer_phone", "").strip(),
                form.get("secondary_customer_email", "").strip(),
                quote_id,
            ),
        )

        course_types = form.get("course_type", [])
        custom_courses = form.get("custom_course_name", [])
        dish_names = form.get("dish_name", [])
        descriptions = form.get("description", [])
        allergens = form.get("allergens", [])
        item_notes = form.get("item_notes", [])
        extra_prices = form.get("extra_price", [])
        menu_groups = form.get("menu_group", [])

        # Starlette FormData returns scalar for single fields; normalize lists.
        if not isinstance(course_types, list):
            course_types = [course_types]
            custom_courses = [custom_courses]
            dish_names = [dish_names]
            descriptions = [descriptions]
            allergens = [allergens]
            item_notes = [item_notes]
            extra_prices = [extra_prices]
            menu_groups = [menu_groups]

        for index, dish_name in enumerate(dish_names):
            dish_name = str(dish_name).strip()
            if not dish_name:
                continue
            price = money(extra_prices[index] if index < len(extra_prices) else 0)
            conn.execute(
                """
                INSERT INTO quote_menu_items(
                    quote_id, menu_group, course_type, custom_course_name, dish_name, description,
                    allergens, notes, is_extra, extra_price, display_order
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    quote_id,
                    str(menu_groups[index] if index < len(menu_groups) else "adult"),
                    str(course_types[index] if index < len(course_types) else "Custom"),
                    str(custom_courses[index] if index < len(custom_courses) else ""),
                    dish_name,
                    str(descriptions[index] if index < len(descriptions) else ""),
                    str(allergens[index] if index < len(allergens) else ""),
                    str(item_notes[index] if index < len(item_notes) else ""),
                    1 if price > 0 else 0,
                    price,
                    index + 1,
                ),
            )
        conn.commit()
    return int(quote_id)


def list_quotes() -> list[Any]:
    return query_all(
        """
        SELECT q.*, c.first_name, c.last_name, c.email, c.phone
        FROM quotes q
        JOIN customers c ON c.id = q.customer_id
        ORDER BY q.created_at DESC
        """
    )


def get_quote(quote_id: int) -> Any:
    return query_one(
        """
        SELECT q.*, c.first_name, c.last_name, c.email, c.phone, c.address, c.fiscal_code, c.notes AS customer_notes,
               s.name AS compiled_by_name, s.role AS compiled_by_role
        FROM quotes q
        JOIN customers c ON c.id = q.customer_id
        LEFT JOIN staff s ON s.id = q.compiled_by_staff_id
        WHERE q.id = ?
        """,
        (quote_id,),
    )


def get_quote_items(quote_id: int) -> list[Any]:
    return query_all(
        "SELECT * FROM quote_menu_items WHERE quote_id = ? ORDER BY display_order ASC, id ASC",
        (quote_id,),
    )


def get_quote_contract(quote_id: int) -> Any:
    return query_one("SELECT * FROM quote_contracts WHERE quote_id = ?", (quote_id,))


def upsert_contract(quote_id: int, form: dict[str, Any]) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO quote_contracts(
                quote_id, iban, account_holder, deposit_amount, deposit_due_date,
                quote_expiry_date, guest_confirmation_date, balance_due_date,
                cancellation_deadline, cancellation_policy, penalty_clause,
                contract_text, accepted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(quote_id) DO UPDATE SET
                iban = excluded.iban,
                account_holder = excluded.account_holder,
                deposit_amount = excluded.deposit_amount,
                deposit_due_date = excluded.deposit_due_date,
                quote_expiry_date = excluded.quote_expiry_date,
                guest_confirmation_date = excluded.guest_confirmation_date,
                balance_due_date = excluded.balance_due_date,
                cancellation_deadline = excluded.cancellation_deadline,
                cancellation_policy = excluded.cancellation_policy,
                penalty_clause = excluded.penalty_clause,
                contract_text = excluded.contract_text,
                accepted_at = excluded.accepted_at,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                quote_id,
                form.get("iban", "").strip(),
                form.get("account_holder", "").strip(),
                money(form.get("deposit_amount")),
                form.get("deposit_due_date", ""),
                form.get("quote_expiry_date", ""),
                form.get("guest_confirmation_date", ""),
                form.get("balance_due_date", ""),
                form.get("cancellation_deadline", ""),
                form.get("cancellation_policy", "").strip(),
                form.get("penalty_clause", "").strip(),
                form.get("contract_text", "").strip(),
                form.get("accepted_at", ""),
            ),
        )
        if form.get("mark_accepted") == "on":
            conn.execute("UPDATE quotes SET status = 'accettato', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (quote_id,))
        conn.commit()


def update_quote_status(quote_id: int, status: str) -> None:
    if status not in STATUSES:
        status = "bozza"
    with get_connection() as conn:
        conn.execute("UPDATE quotes SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (status, quote_id))
        conn.commit()


def dashboard_stats() -> dict[str, Any]:
    rows = query_all("SELECT status, COUNT(*) AS count FROM quotes GROUP BY status")
    stats = {row["status"]: row["count"] for row in rows}
    total = query_one("SELECT COUNT(*) AS count, COALESCE(SUM(total_amount), 0) AS value FROM quotes")
    return {
        "by_status": stats,
        "total_quotes": total["count"] if total else 0,
        "total_value": total["value"] if total else 0,
    }


def default_contract_template(data: dict[str, str]) -> str:
    return f"""CONDIZIONI DI CONFERMA DEL PREVENTIVO

Il presente preventivo si intende valido fino al giorno {data.get('quote_expiry_date', '[DATA_SCADENZA_PREVENTIVO]')}.
La conferma dell'evento dovrà avvenire mediante accettazione scritta del presente preventivo e versamento di una caparra confirmatoria pari a € {data.get('deposit_amount', '[IMPORTO_CAPARRA]')}, da imputarsi al corrispettivo finale dell'evento.

Il pagamento della caparra dovrà essere effettuato tramite bonifico bancario alle seguenti coordinate:
Intestatario: {data.get('account_holder', '[INTESTATARIO_CONTO]')}
IBAN: {data.get('iban', '[IBAN]')}
Causale: Conferma evento {data.get('event_type', '[TIPO_EVENTO]')} del {data.get('event_date', '[DATA_EVENTO]')} - {data.get('customer_name', '[NOME_CLIENTE]')}

Il saldo residuo dovrà essere corrisposto entro e non oltre il giorno {data.get('balance_due_date', '[DATA_SALDO]')}, salvo diverso accordo scritto tra le parti.

Il numero definitivo degli invitati dovrà essere comunicato entro il giorno {data.get('guest_confirmation_date', '[DATA_CONFERMA_INVITATI]')}. Eventuali variazioni successive potranno essere accettate compatibilmente con le esigenze organizzative della struttura.

In caso di annullamento dell'evento da parte del cliente oltre il termine del {data.get('cancellation_deadline', '[DATA_LIMITE_ANNULLAMENTO]')}, la struttura si riserva il diritto di trattenere la caparra confirmatoria versata, fatto salvo l'eventuale maggior danno documentabile o quanto diversamente concordato per iscritto.

Eventuali servizi aggiuntivi richiesti successivamente all'accettazione del presente preventivo saranno oggetto di integrazione economica separata.

Il presente preventivo diventa vincolante solo a seguito di accettazione scritta da parte del cliente e ricezione della caparra confirmatoria.

Luogo e data: ______________________

Firma cliente: ______________________

Firma struttura: ______________________
"""


# === EDIT / DELETE QUOTE PATCH ===

def update_quote(quote_id: int, form: dict[str, Any]) -> None:
    existing = get_quote(quote_id)
    if existing is None:
        raise ValueError("Preventivo non trovato")

    guests_adults = integer(form.get("guests_adults"))
    guests_children = integer(form.get("guests_children"))
    price_per_adult = money(form.get("price_per_adult"))
    price_per_child = money(form.get("price_per_child"))
    extra_amount = money(form.get("extra_amount"))
    discount_amount = money(form.get("discount_amount"))
    vat_rate = money(form.get("vat_rate"))

    total_amount = calculate_total(
        guests_adults,
        guests_children,
        price_per_adult,
        price_per_child,
        extra_amount,
        discount_amount,
        vat_rate,
    )

    customer_id = existing["customer_id"]

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE customers
            SET first_name = ?,
                last_name = ?,
                phone = ?,
                email = ?,
                address = ?,
                fiscal_code = ?,
                notes = ?
            WHERE id = ?
            """,
            (
                form.get("customer_first_name", "").strip(),
                form.get("customer_last_name", "").strip(),
                form.get("customer_phone", "").strip(),
                form.get("customer_email", "").strip(),
                form.get("customer_address", "").strip(),
                form.get("customer_fiscal_code", "").strip(),
                form.get("customer_notes", "").strip(),
                customer_id,
            ),
        )

        conn.execute(
            """
            UPDATE quotes
            SET event_type = ?,
                custom_event_type = ?,
                event_date = ?,
                event_start_time = ?,
                event_end_time = ?,
                guests_adults = ?,
                guests_children = ?,
                location = ?,
                compiled_by_staff_id = ?,
                price_per_adult = ?,
                price_per_child = ?,
                extra_amount = ?,
                discount_amount = ?,
                vat_rate = ?,
                total_amount = ?,
                notes = ?,
                primary_customer_role = ?,
                secondary_customer_role = ?,
                secondary_customer_first_name = ?,
                secondary_customer_last_name = ?,
                secondary_customer_phone = ?,
                secondary_customer_email = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                form.get("event_type", "Generico"),
                form.get("custom_event_type", "").strip(),
                form.get("event_date", ""),
                form.get("event_start_time", ""),
                form.get("event_end_time", ""),
                guests_adults,
                guests_children,
                form.get("location", "").strip(),
                integer(form.get("compiled_by_staff_id")) or None,
                price_per_adult,
                price_per_child,
                extra_amount,
                discount_amount,
                vat_rate,
                total_amount,
                form.get("notes", "").strip(),
                form.get("primary_customer_role", "").strip(),
                form.get("secondary_customer_role", "").strip(),
                form.get("secondary_customer_first_name", "").strip(),
                form.get("secondary_customer_last_name", "").strip(),
                form.get("secondary_customer_phone", "").strip(),
                form.get("secondary_customer_email", "").strip(),
                quote_id,
            ),
        )

        conn.execute("DELETE FROM quote_menu_items WHERE quote_id = ?", (quote_id,))

        course_types = form.get("course_type", [])
        custom_courses = form.get("custom_course_name", [])
        dish_names = form.get("dish_name", [])
        descriptions = form.get("description", [])
        allergens = form.get("allergens", [])
        item_notes = form.get("item_notes", [])
        extra_prices = form.get("extra_price", [])
        menu_groups = form.get("menu_group", [])

        if not isinstance(course_types, list):
            course_types = [course_types]
            custom_courses = [custom_courses]
            dish_names = [dish_names]
            descriptions = [descriptions]
            allergens = [allergens]
            item_notes = [item_notes]
            extra_prices = [extra_prices]
            menu_groups = [menu_groups]

        for index, dish_name in enumerate(dish_names):
            dish_name = str(dish_name).strip()
            if not dish_name:
                continue

            price = money(extra_prices[index] if index < len(extra_prices) else 0)

            conn.execute(
                """
                INSERT INTO quote_menu_items(
                    quote_id, menu_group, course_type, custom_course_name, dish_name, description,
                    allergens, notes, is_extra, extra_price, display_order
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    quote_id,
                    str(menu_groups[index] if index < len(menu_groups) else "adult"),
                    str(course_types[index] if index < len(course_types) else "Custom"),
                    str(custom_courses[index] if index < len(custom_courses) else ""),
                    dish_name,
                    str(descriptions[index] if index < len(descriptions) else ""),
                    str(allergens[index] if index < len(allergens) else ""),
                    str(item_notes[index] if index < len(item_notes) else ""),
                    1 if price > 0 else 0,
                    price,
                    index + 1,
                ),
            )

        conn.commit()


def delete_quote(quote_id: int) -> None:
    existing = get_quote(quote_id)
    if existing is None:
        return

    customer_id = existing["customer_id"]

    with get_connection() as conn:
        conn.execute("DELETE FROM quotes WHERE id = ?", (quote_id,))

        # Elimina il cliente solo se non è più collegato ad altri preventivi.
        still_used = conn.execute(
            "SELECT COUNT(*) AS c FROM quotes WHERE customer_id = ?",
            (customer_id,),
        ).fetchone()["c"]

        if still_used == 0:
            conn.execute("DELETE FROM customers WHERE id = ?", (customer_id,))

        conn.commit()


# === DUPLICATE QUOTE PATCH ===

def duplicate_quote(quote_id: int) -> int:
    source = get_quote(quote_id)
    if source is None:
        raise ValueError("Preventivo non trovato")

    def row_get(row: Any, key: str, default: Any = "") -> Any:
        try:
            return row[key] if key in row.keys() and row[key] is not None else default
        except Exception:
            return default

    new_quote_number, year, progressive = next_quote_number()
    source_items = get_quote_items(quote_id)
    source_contract = get_quote_contract(quote_id)

    with get_connection() as conn:
        new_customer_id = conn.execute(
            """
            INSERT INTO customers(first_name, last_name, phone, email, address, fiscal_code, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row_get(source, "first_name"),
                row_get(source, "last_name"),
                row_get(source, "phone"),
                row_get(source, "email"),
                row_get(source, "address"),
                row_get(source, "fiscal_code"),
                row_get(source, "customer_notes"),
            ),
        ).lastrowid

        new_quote_id = conn.execute(
            """
            INSERT INTO quotes(
                quote_number, year, progressive_number, customer_id,
                event_type, custom_event_type, event_date, event_start_time, event_end_time,
                guests_adults, guests_children, location, status, compiled_by_staff_id,
                price_per_adult, price_per_child, extra_amount, discount_amount, vat_rate,
                total_amount, notes, primary_customer_role,
                secondary_customer_role, secondary_customer_first_name, secondary_customer_last_name,
                secondary_customer_phone, secondary_customer_email
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_quote_number,
                year,
                progressive,
                new_customer_id,
                row_get(source, "event_type", "Generico"),
                row_get(source, "custom_event_type"),
                row_get(source, "event_date"),
                row_get(source, "event_start_time"),
                row_get(source, "event_end_time"),
                int(row_get(source, "guests_adults", 0) or 0),
                int(row_get(source, "guests_children", 0) or 0),
                row_get(source, "location"),
                "bozza",
                row_get(source, "compiled_by_staff_id", None),
                float(row_get(source, "price_per_adult", 0) or 0),
                float(row_get(source, "price_per_child", 0) or 0),
                float(row_get(source, "extra_amount", 0) or 0),
                float(row_get(source, "discount_amount", 0) or 0),
                float(row_get(source, "vat_rate", 0) or 0),
                float(row_get(source, "total_amount", 0) or 0),
                row_get(source, "notes"),
                row_get(source, "primary_customer_role"),
                row_get(source, "secondary_customer_role"),
                row_get(source, "secondary_customer_first_name"),
                row_get(source, "secondary_customer_last_name"),
                row_get(source, "secondary_customer_phone"),
                row_get(source, "secondary_customer_email"),
            ),
        ).lastrowid

        for index, item in enumerate(source_items):
            conn.execute(
                """
                INSERT INTO quote_menu_items(
                    quote_id, menu_group, course_type, custom_course_name, dish_name, description,
                    allergens, notes, is_extra, extra_price, display_order
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_quote_id,
                    row_get(item, "menu_group", "adult"),
                    row_get(item, "course_type", "Custom"),
                    row_get(item, "custom_course_name"),
                    row_get(item, "dish_name"),
                    row_get(item, "description"),
                    row_get(item, "allergens"),
                    row_get(item, "notes"),
                    int(row_get(item, "is_extra", 0) or 0),
                    float(row_get(item, "extra_price", 0) or 0),
                    index + 1,
                ),
            )

        if source_contract:
            conn.execute(
                """
                INSERT INTO quote_contracts(
                    quote_id, iban, account_holder, deposit_amount, deposit_due_date,
                    quote_expiry_date, guest_confirmation_date, balance_due_date,
                    cancellation_deadline, cancellation_policy, penalty_clause,
                    contract_text, accepted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_quote_id,
                    row_get(source_contract, "iban"),
                    row_get(source_contract, "account_holder"),
                    float(row_get(source_contract, "deposit_amount", 0) or 0),
                    row_get(source_contract, "deposit_due_date"),
                    row_get(source_contract, "quote_expiry_date"),
                    row_get(source_contract, "guest_confirmation_date"),
                    row_get(source_contract, "balance_due_date"),
                    row_get(source_contract, "cancellation_deadline"),
                    row_get(source_contract, "cancellation_policy"),
                    row_get(source_contract, "penalty_clause"),
                    row_get(source_contract, "contract_text"),
                    "",
                ),
            )

        conn.commit()

    return int(new_quote_id)

