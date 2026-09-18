"""Консольная проверка: партнеры из БД с текущим процентом скидки."""

from contextlib import closing

from db import get_connection
from partner_service import get_partner_ids, get_partner_with_discount


def main():
    with closing(get_connection()) as connection:
        for partner_id in get_partner_ids(connection):
            print(get_partner_with_discount(connection, partner_id))


if __name__ == "__main__":
    main()
