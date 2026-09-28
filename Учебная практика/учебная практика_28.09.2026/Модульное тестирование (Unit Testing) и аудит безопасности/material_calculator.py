"""Ядро расчета сырья: сколько материала нужно на партию продукции."""

import math
from decimal import ROUND_CEILING, Decimal

ERROR_RESULT = -1

QUANTITY_PROBLEM = (
    "Количество продукции должно быть целым числом больше 0.\n\n"
    "Пожалуйста, введите число штук без знаков препинания, например "
    "250, и повторите расчет.")
PARAMETERS_PROBLEM = (
    "Параметры продукции должны быть положительными числами.\n\n"
    "Пожалуйста, введите оба параметра больше нуля, например 2,5, и "
    "повторите расчет.")
PRODUCT_TYPE_PROBLEM = (
    "Такого типа продукции нет в справочнике.\n\n"
    "Пожалуйста, выберите тип продукции из списка и повторите расчет.")
MATERIAL_TYPE_PROBLEM = (
    "Такого типа материала нет в справочнике.\n\n"
    "Пожалуйста, выберите тип материала из списка и повторите расчет.")

PRODUCT_TYPE_QUERY = "SELECT coefficient FROM product_types WHERE id = %s"
MATERIAL_TYPE_QUERY = "SELECT defect_percent FROM material_types WHERE id = %s"
PRODUCT_TYPES_QUERY = """
    SELECT id, name, coefficient
    FROM product_types
    ORDER BY name
"""
MATERIAL_TYPES_QUERY = """
    SELECT id, name, defect_percent
    FROM material_types
    ORDER BY name
"""


def first_value(row):
    """Первое значение строки результата или None, если строки нет."""
    if row is None:
        return None
    return row[0]


class DatabaseCatalog:
    """Справочники типов продукции и материалов в базе данных."""

    def __init__(self, connection):
        self.connection = connection

    def product_type_coefficient(self, product_type_id: int):
        """Коэффициент типа продукции или None, если типа нет."""
        with self.connection.cursor() as cursor:
            cursor.execute(PRODUCT_TYPE_QUERY, (product_type_id,))
            return first_value(cursor.fetchone())

    def material_defect_percent(self, material_type_id: int):
        """Процент брака материала или None, если типа нет."""
        with self.connection.cursor() as cursor:
            cursor.execute(MATERIAL_TYPE_QUERY, (material_type_id,))
            return first_value(cursor.fetchone())


class MemoryCatalog:
    """Справочники в памяти — мок-объект вместо базы данных.

    Нужен, чтобы проверить метод расчета без PostgreSQL: ключи — id
    типов, значения — коэффициент типа или процент брака.
    """

    def __init__(self, coefficients: dict, defect_percents: dict):
        self.coefficients = coefficients
        self.defect_percents = defect_percents

    def product_type_coefficient(self, product_type_id: int):
        """Коэффициент типа продукции или None, если типа нет."""
        return self.coefficients.get(product_type_id)

    def material_defect_percent(self, material_type_id: int):
        """Процент брака материала или None, если типа нет."""
        return self.defect_percents.get(material_type_id)


def is_whole_number(value) -> bool:
    """Целое число; True и False не подходят, хотя bool в Python — int."""
    return isinstance(value, int) and not isinstance(value, bool)


def is_positive_number(value) -> bool:
    """Конечное число больше нуля; NaN и бесконечность не подходят."""
    if isinstance(value, bool):
        return False
    if not isinstance(value, (int, float, Decimal)):
        return False
    return math.isfinite(value) and value > 0


def is_valid_quantity(quantity) -> bool:
    """Количество продукции — целое и больше нуля."""
    return is_whole_number(quantity) and quantity > 0


def are_valid_parameters(param_1, param_2) -> bool:
    """Оба параметра продукции — положительные числа."""
    return is_positive_number(param_1) and is_positive_number(param_2)


def as_decimal(value) -> Decimal:
    """Перевести число в Decimal без погрешности двоичной дроби.

    Через строку: Decimal(2.35) дал бы 2.350000000000000088817...,
    а Decimal("2.35") — ровно 2.35.
    """
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


class MaterialCalculator:
    """Расчет количества материала на партию продукции с учетом брака.

    Справочники передаются снаружи: в приложении это DatabaseCatalog,
    в проверках без базы — MemoryCatalog.
    """

    def __init__(self, catalog):
        self.catalog = catalog

    def calculate_material(self, product_type_id: int, material_type_id: int,
                           quantity: int, param_1: float,
                           param_2: float) -> int:
        """Вернуть количество материала или -1, если данные неверны.

        1. Базовый расход на 1 ед. = param_1 × param_2 × коэффициент
           типа продукции.
        2. Общий чистый расход = базовый расход × quantity.
        3. Итог с учетом брака = чистый расход × (1 + брак % / 100).
        4. Итог округляется до целого в большую сторону.

        Несуществующий тип, параметры не больше нуля или количество
        не больше нуля дают -1 вместо исключения.
        """
        if not is_valid_quantity(quantity):
            return ERROR_RESULT
        if not are_valid_parameters(param_1, param_2):
            return ERROR_RESULT
        coefficient = self.lookup(self.catalog.product_type_coefficient,
                                  product_type_id)
        defect_percent = self.lookup(self.catalog.material_defect_percent,
                                     material_type_id)
        if coefficient is None or defect_percent is None:
            return ERROR_RESULT
        unit_amount = (as_decimal(param_1) * as_decimal(param_2)
                       * as_decimal(coefficient))
        net_amount = unit_amount * quantity
        total_amount = net_amount * (1 + as_decimal(defect_percent) / 100)
        # Считаем в Decimal, а не во float: во float 100 × 1.1 дает
        # 110.00000000000001, и округление вверх выдало бы 111 вместо 110.
        return int(total_amount.to_integral_value(rounding=ROUND_CEILING))

    def find_problem(self, product_type_id: int, material_type_id: int,
                     quantity: int, param_1: float, param_2: float):
        """Объяснить, почему расчет вернул -1; None — данные в порядке.

        Проверки те же, что в calculate_material, поэтому окно может
        показать менеджеру точную причину и что с ней сделать.
        """
        if not is_valid_quantity(quantity):
            return QUANTITY_PROBLEM
        if not are_valid_parameters(param_1, param_2):
            return PARAMETERS_PROBLEM
        if self.lookup(self.catalog.product_type_coefficient,
                       product_type_id) is None:
            return PRODUCT_TYPE_PROBLEM
        if self.lookup(self.catalog.material_defect_percent,
                       material_type_id) is None:
            return MATERIAL_TYPE_PROBLEM
        return None

    def lookup(self, read, type_id):
        """Значение справочника по id или None, если такого типа нет.

        Нецелый id в базу не отправляется: такого типа заведомо нет, а
        запрос с текстом вместо числа закончился бы ошибкой СУБД.
        """
        if not is_whole_number(type_id):
            return None
        return read(type_id)


def get_product_types(connection) -> list[dict]:
    """Вернуть справочник типов продукции для выпадающего списка."""
    with connection.cursor() as cursor:
        cursor.execute(PRODUCT_TYPES_QUERY)
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
    return [dict(zip(columns, row)) for row in rows]


def get_material_types(connection) -> list[dict]:
    """Вернуть справочник типов материалов для выпадающего списка."""
    with connection.cursor() as cursor:
        cursor.execute(MATERIAL_TYPES_QUERY)
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
    return [dict(zip(columns, row)) for row in rows]
