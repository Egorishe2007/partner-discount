"""Ядро бизнес-логики: расчет индивидуальной скидки партнера."""


def calculate_partner_discount(total_quantity: int) -> int:
    """Вернуть процент скидки партнера по объему купленной продукции.

    Критерии из ТЗ:
        менее 10 000 ед.        -> 0 %
        от 10 000 до 49 999     -> 5 %
        от 50 000 до 299 999    -> 10 %
        от 300 000 и более      -> 15 %
    """
    if total_quantity < 0:
        raise ValueError("Объем продукции не может быть отрицательным")
    if total_quantity < 10_000:
        return 0
    if total_quantity < 50_000:
        return 5
    if total_quantity < 300_000:
        return 10
    return 15
