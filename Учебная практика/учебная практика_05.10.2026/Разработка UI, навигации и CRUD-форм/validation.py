"""Проверка данных карточки партнера перед отправкой в базу."""

import re

# Поле, его название на форме и что сделать менеджеру, если оно пустое.
REQUIRED_FIELDS = (
    ("name", "Наименование",
     "введите название организации без формы собственности, например "
     "Вектор"),
    ("inn", "ИНН", "введите 10 или 12 цифр без пробелов"),
    ("email", "Электронная почта",
     "укажите адрес вида partner@example.com"),
)
# Директор, телефон и адрес в базе необязательны: у партнеров из файлов
# заказчика их нет, менеджер дополнит карточку позже.
OPTIONAL_FIELDS = ("director", "phone", "legal_address")
# Длины столбцов из schema.sql: более длинное значение СУБД не примет.
MAX_LENGTHS = {
    "name": ("Наименование", 255),
    "email": ("Электронная почта", 255),
    "director": ("ФИО директора", 255),
    "phone": ("Телефон", 20),
    "legal_address": ("Юридический адрес", 500),
}
INN_PATTERN = re.compile(r"^(\d{10}|\d{12})$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")

RATING_MESSAGE = (
    "Рейтинг должен быть целым числом от 0.\n\n"
    "Пожалуйста, удалите из поля знаки препинания, буквы и пробелы, "
    "оставьте только цифры и повторите попытку.")
INN_MESSAGE = (
    "ИНН должен состоять из 10 или 12 цифр.\n\n"
    "Пожалуйста, удалите из поля пробелы, буквы и другие знаки и "
    "повторите сохранение.")
EMAIL_MESSAGE = (
    "Электронная почта указана неверно.\n\n"
    "Пожалуйста, введите адрес вида partner@example.com: имя, знак «@» и "
    "домен с точкой. Затем повторите сохранение.")


class ValidationError(Exception):
    """Данные карточки не прошли проверку."""


def checked_values(values: dict) -> dict:
    """Проверить поля карточки и вернуть значения, готовые к записи.

    Возвращает копию значений: лишние пробелы убраны, пустые
    необязательные поля стали None, почта — в нижнем регистре, рейтинг —
    числом. При первой же проблеме бросает ValidationError с текстом,
    который можно показать менеджеру как есть.
    """
    checked = dict(values)
    for key, caption, advice in REQUIRED_FIELDS:
        checked[key] = str(checked.get(key) or "").strip()
        if not checked[key]:
            raise ValidationError(
                f"Поле «{caption}» не заполнено.\n\n"
                f"Пожалуйста, {advice} и повторите сохранение.")
    for key in OPTIONAL_FIELDS:
        # Пустое поле уходит в базу как NULL, а не как пустая строка:
        # иначе «не указан» и «указан пустым» стали бы разными данными.
        checked[key] = str(checked.get(key) or "").strip() or None
    for key, (caption, limit) in MAX_LENGTHS.items():
        if checked[key] is not None and len(checked[key]) > limit:
            raise ValidationError(
                f"Поле «{caption}» длиннее {limit} символов.\n\n"
                f"Пожалуйста, сократите значение и повторите сохранение.")
    if not INN_PATTERN.match(checked["inn"]):
        raise ValidationError(INN_MESSAGE)
    # Регистр в адресе почты не важен, а UNIQUE в базе его различает:
    # без приведения Alpha@Gmail.com и alpha@gmail.com считались бы
    # разными партнерами.
    checked["email"] = checked["email"].lower()
    if not EMAIL_PATTERN.match(checked["email"]):
        raise ValidationError(EMAIL_MESSAGE)
    checked["rating"] = checked_rating(checked.get("rating"))
    return checked


def checked_rating(rating) -> int:
    """Вернуть рейтинг целым неотрицательным числом.

    Пустое поле, буквы, знаки препинания и минус приводят к
    ValidationError: в базе рейтинг объявлен как INTEGER с проверкой
    rating >= 0, и запрос с таким значением просто не выполнился бы.
    """
    try:
        number = int(str(rating).strip())
    except (TypeError, ValueError):
        raise ValidationError(RATING_MESSAGE) from None
    if number < 0:
        raise ValidationError(RATING_MESSAGE)
    return number
