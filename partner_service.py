"""Данные партнера из БД, дополненные текущим процентом скидки."""

from partner_discount import calculate_partner_discount

PARTNER_SALES_QUERY = """
    SELECT p.id,
           p.partner_type,
           p.name,
           p.director,
           p.email,
           p.phone,
           p.rating,
           COALESCE(SUM(s.quantity), 0) AS total_quantity
    FROM partners AS p
    LEFT JOIN sales_history AS s ON s.partner_id = p.id
    WHERE p.id = %s
    GROUP BY p.id, p.partner_type, p.name, p.director,
             p.email, p.phone, p.rating
"""


def get_partner_ids(connection) -> list[int]:
    """Вернуть идентификаторы всех партнеров по порядку."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT id FROM partners ORDER BY id")
        return [row[0] for row in cursor.fetchall()]


def get_partner_sales(connection, partner_id: int) -> dict | None:
    """Вернуть данные партнера и суммарный объем его продаж."""
    with connection.cursor() as cursor:
        cursor.execute(PARTNER_SALES_QUERY, (partner_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        columns = [column.name for column in cursor.description]
    return dict(zip(columns, row))


def get_partner_with_discount(connection, partner_id: int) -> dict | None:
    """Вернуть данные партнера, дополненные текущим процентом скидки."""
    partner = get_partner_sales(connection, partner_id)
    if partner is None:
        return None
    total_quantity = partner["total_quantity"]
    partner["discount_percent"] = calculate_partner_discount(total_quantity)
    return partner
