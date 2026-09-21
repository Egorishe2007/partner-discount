"""Данные партнеров из БД, дополненные текущим процентом скидки."""

from partner_discount import calculate_partner_discount

PARTNER_COLUMNS = """
           p.id,
           p.partner_type,
           p.name,
           p.director,
           p.email,
           p.phone,
           p.legal_address,
           p.inn,
           p.rating,
           COALESCE(SUM(s.quantity), 0) AS total_quantity
"""

PARTNER_GROUP_BY = """
    GROUP BY p.id, p.partner_type, p.name, p.director, p.email,
             p.phone, p.legal_address, p.inn, p.rating
"""

PARTNER_SALES_QUERY = f"""
    SELECT {PARTNER_COLUMNS}
    FROM partners AS p
    LEFT JOIN sales_history AS s ON s.partner_id = p.id
    WHERE p.id = %s
    {PARTNER_GROUP_BY}
"""

PARTNERS_LIST_QUERY = f"""
    SELECT {PARTNER_COLUMNS}
    FROM partners AS p
    LEFT JOIN sales_history AS s ON s.partner_id = p.id
    {PARTNER_GROUP_BY}
    ORDER BY p.name
"""


def add_discount(partner: dict) -> dict:
    """Дополнить данные партнера его текущим процентом скидки.

    Если истории продаж нет, SUM(quantity) дает NULL (в Python None),
    поэтому объем приводится к 0: иначе расчет упал бы с TypeError.
    """
    total_quantity = partner["total_quantity"] or 0
    partner["total_quantity"] = total_quantity
    partner["discount_percent"] = calculate_partner_discount(total_quantity)
    return partner


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
        columns = [column[0] for column in cursor.description]
    return dict(zip(columns, row))


def get_partner_with_discount(connection, partner_id: int) -> dict | None:
    """Вернуть данные партнера, дополненные текущим процентом скидки."""
    partner = get_partner_sales(connection, partner_id)
    if partner is None:
        return None
    return add_discount(partner)


def get_partners_with_discounts(connection) -> list[dict]:
    """Вернуть всех партнеров с объемом продаж и процентом скидки."""
    with connection.cursor() as cursor:
        cursor.execute(PARTNERS_LIST_QUERY)
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
    return [add_discount(dict(zip(columns, row))) for row in rows]


PARTNER_INSERT = """
    INSERT INTO partners (partner_type, name, director, email, phone,
                          legal_address, inn, rating)
    VALUES (%(partner_type)s, %(name)s, %(director)s, %(email)s,
            %(phone)s, %(legal_address)s, %(inn)s, %(rating)s)
    RETURNING id
"""

PARTNER_UPDATE = """
    UPDATE partners
       SET partner_type = %(partner_type)s,
           name = %(name)s,
           director = %(director)s,
           email = %(email)s,
           phone = %(phone)s,
           legal_address = %(legal_address)s,
           inn = %(inn)s,
           rating = %(rating)s
     WHERE id = %(id)s
"""


def insert_partner(connection, values: dict) -> int:
    """Добавить партнера и вернуть id созданной записи.

    RETURNING id отдает ключ сразу: карточка запоминает его и при
    следующем сохранении делает UPDATE, а не второй INSERT.
    """
    with connection.cursor() as cursor:
        cursor.execute(PARTNER_INSERT, values)
        partner_id = cursor.fetchone()[0]
    connection.commit()
    return partner_id


def update_partner(connection, partner_id: int, values: dict) -> bool:
    """Обновить партнера по id; False — если такой записи уже нет.

    Обновление идет по первичному ключу, а не по названию: история
    продаж ссылается на тот же id, поэтому переименование партнера
    не рвет связь с его отгрузками.
    """
    with connection.cursor() as cursor:
        cursor.execute(PARTNER_UPDATE, dict(values, id=partner_id))
        updated = cursor.rowcount
    connection.commit()
    return updated == 1
