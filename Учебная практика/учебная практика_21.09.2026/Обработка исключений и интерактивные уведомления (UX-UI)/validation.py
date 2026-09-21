"""Проверка данных карточки партнера перед отправкой в базу."""

# Поле, его название на форме и что сделать менеджеру, если оно пустое.
REQUIRED_FIELDS = (
    ("name", "Наименование", "введите название организации"),
    ("email", "Электронная почта",
     "укажите адрес вида partner@example.com"),
    ("director", "ФИО директора", "введите фамилию, имя и отчество"),
    ("phone", "Телефон", "введите номер вида +7 900 000 00 00"),
    ("inn", "ИНН", "введите 10 или 12 цифр без пробелов"),
    ("legal_address", "Юридический адрес",
     "введите город, улицу и номер дома"),
)

RATING_MESSAGE = (
    "Рейтинг должен быть целым числом от 0.\n\n"
    "Пожалуйста, удалите из поля знаки препинания, буквы и пробелы, "
    "оставьте только цифры и повторите попытку.")
EMAIL_MESSAGE = (
    "Электронная почта указана без знака «@».\n\n"
    "Пожалуйста, введите адрес вида partner@example.com и повторите "
    "сохранение.")


class ValidationError(Exception):
    """Данные карточки не прошли проверку."""


def checked_values(values: dict) -> dict:
    """Проверить поля карточки и вернуть значения, готовые к записи.

    Возвращает копию значений: лишние пробелы убраны, рейтинг приведен
    к числу. При первой же проблеме бросает ValidationError с текстом,
    который можно показать менеджеру как есть.
    """
    checked = dict(values)
    for key, caption, advice in REQUIRED_FIELDS:
        checked[key] = str(checked.get(key, "")).strip()
        if not checked[key]:
            raise ValidationError(
                f"Поле «{caption}» не заполнено.\n\n"
                f"Пожалуйста, {advice} и повторите сохранение.")
    if "@" not in checked["email"]:
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
