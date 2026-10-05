"""Проверка данных карточки партнера перед отправкой в базу."""

import re

from messages import instructions

# Поле, его название на форме и что в него ввести.
REQUIRED_FIELDS = (
    ("name", "Наименование",
     "Введите название организации без формы собственности, например "
     "Вектор, или фамилию и инициалы для ИП."),
    ("inn", "ИНН", "Введите 10 цифр для организации или 12 — для ИП."),
    ("email", "Электронная почта",
     "Введите рабочий адрес вида partner@example.com."),
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
SAVE_STEP = "Нажмите «Сохранить» еще раз."

RATING_MESSAGE = instructions(
    "Рейтинг должен быть целым числом от 0.",
    "Удалите из поля «Рейтинг» буквы, пробелы и знаки препинания — "
    "точку, запятую, минус.",
    "Введите целое число, например 7.",
    SAVE_STEP)
INN_MESSAGE = instructions(
    "ИНН должен состоять из 10 или 12 цифр.",
    "Удалите из поля «ИНН» пробелы, буквы и другие знаки.",
    "Проверьте, что осталось 10 цифр для организации или 12 — для ИП.",
    SAVE_STEP)
EMAIL_MESSAGE = instructions(
    "Электронная почта указана неверно.",
    "Проверьте, что в адресе есть имя, знак «@» и домен с точкой, например "
    "partner@example.com.",
    "Удалите из адреса пробелы.",
    SAVE_STEP)


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
            raise ValidationError(instructions(
                f"Поле «{caption}» не заполнено.",
                f"Перейдите в поле «{caption}».", advice, SAVE_STEP))
    for key in OPTIONAL_FIELDS:
        # Пустое поле уходит в базу как NULL, а не как пустая строка:
        # иначе «не указан» и «указан пустым» стали бы разными данными.
        checked[key] = str(checked.get(key) or "").strip() or None
    for key, (caption, limit) in MAX_LENGTHS.items():
        if checked[key] is not None and len(checked[key]) > limit:
            raise ValidationError(instructions(
                f"Поле «{caption}» длиннее {limit} символов.",
                f"Сократите значение поля «{caption}» до {limit} символов.",
                SAVE_STEP))
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
