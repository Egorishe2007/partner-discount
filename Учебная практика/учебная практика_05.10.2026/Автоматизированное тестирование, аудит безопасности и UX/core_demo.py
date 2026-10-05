"""Консольная проверка ядра: скидки партнеров и расчет сырья по базе."""

from contextlib import closing

from db import get_connection
from material_calculator import DatabaseCatalog, MaterialCalculator
from partner_service import get_partner_discount, get_partners_with_discounts

# Тип продукции, тип материала, количество, параметр 1, параметр 2.
MATERIAL_EXAMPLES = (
    (1, 1, 250, 2.5, 1.2),
    (3, 2, 100, 1.5, 0.8),
    (4, 5, 40, 3.0, 2.0),
    (99, 1, 250, 2.5, 1.2),
    (1, 0, 250, 2.5, 1.2),
    (1, 1, 250, -2.5, 1.2),
    (1, 1, 0, 2.5, 1.2),
)


def print_discounts(connection):
    """Скидка каждого партнера по объему продаж из базы."""
    print("Скидки партнеров:")
    for partner in get_partners_with_discounts(connection):
        title = f'{partner["partner_type"]} {partner["name"]}'
        print(f'  {title:<18} продано {partner["total_quantity"]:>3} шт. '
              f'-> {partner["discount_percent"]} %')
    print(f"  партнер 999: {get_partner_discount(connection, 999)}")


def print_materials(connection):
    """Расход сырья по справочникам из базы; -1 — неверные данные."""
    calculator = MaterialCalculator(DatabaseCatalog(connection))
    print("Расчет материалов (тип прод., тип мат., кол-во, п1, п2):")
    for example in MATERIAL_EXAMPLES:
        result = calculator.calculate_material(*example)
        print(f"  {example} -> {result}")


def main():
    with closing(get_connection()) as connection:
        print_discounts(connection)
        print_materials(connection)


if __name__ == "__main__":
    main()
