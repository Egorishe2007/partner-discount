"""Консольная проверка метода расчета материалов.

python material_demo.py         — справочники берутся из базы данных;
python material_demo.py --mock  — те же значения, что в schema.sql,
                                  но без PostgreSQL (мок-объект).
"""

import sys
from contextlib import closing
from decimal import Decimal

from db import get_connection
from material_calculator import (DatabaseCatalog, MaterialCalculator,
                                 MemoryCatalog)

MOCK_COEFFICIENTS = {
    1: Decimal("2.35"),
    2: Decimal("5.15"),
    3: Decimal("4.34"),
    4: Decimal("1.50"),
}
MOCK_DEFECT_PERCENTS = {
    1: Decimal("0.10"),
    2: Decimal("0.95"),
    3: Decimal("0.28"),
    4: Decimal("0.55"),
    5: Decimal("0.34"),
}

# Тип продукции, тип материала, количество, параметр 1, параметр 2.
EXAMPLES = (
    (1, 1, 250, 2.5, 1.2),
    (3, 2, 100, 1.5, 0.8),
    (4, 5, 40, 3.0, 2.0),
    (1, 1, 0, 2.5, 1.2),
    (1, 1, 250, -2.5, 1.2),
    (99, 1, 250, 2.5, 1.2),
    (1, 0, 250, 2.5, 1.2),
)


def print_examples(calculator: MaterialCalculator):
    """Посчитать примеры и вывести входные данные рядом с результатом."""
    print("Тип прод. | Тип мат. | Кол-во | Парам. 1 | Парам. 2 | Материал")
    for example in EXAMPLES:
        result = calculator.calculate_material(*example)
        product_type_id, material_type_id, quantity, param_1, param_2 = (
            example)
        print(f"{product_type_id:>9} | {material_type_id:>8} | "
              f"{quantity:>6} | {param_1:>8} | {param_2:>8} | {result:>8}")


def main():
    if "--mock" in sys.argv:
        catalog = MemoryCatalog(MOCK_COEFFICIENTS, MOCK_DEFECT_PERCENTS)
        print_examples(MaterialCalculator(catalog))
        return
    with closing(get_connection()) as connection:
        print_examples(MaterialCalculator(DatabaseCatalog(connection)))


if __name__ == "__main__":
    main()
