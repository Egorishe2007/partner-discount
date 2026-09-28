"""Журнал ошибок приложения: дата, время и текст ошибки в app.log."""

import logging
import os

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "app.log")
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(message)s"
DATE_FORMAT = "%d.%m.%Y %H:%M:%S"
ROOT_NAME = "crm"

# Пока журнал не настроен (например, в тестах), записи тихо
# отбрасываются, а не сыплются в консоль.
logging.getLogger(ROOT_NAME).addHandler(logging.NullHandler())


def get_logger(module_name: str) -> logging.Logger:
    """Журнал для модуля приложения: все записи идут в общий файл."""
    return logging.getLogger(f"{ROOT_NAME}.{module_name}")


def setup_logging(path: str = LOG_FILE) -> logging.Handler:
    """Начать писать журнал в файл; вернуть обработчик записи."""
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    logger = logging.getLogger(ROOT_NAME)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    return handler


def first_line(error: Exception) -> str:
    """Первая строка текста ошибки: у psycopg2 он бывает многострочным."""
    lines = str(error).strip().splitlines()
    if not lines:
        return type(error).__name__
    return lines[0]
