"""Тексты сообщений об ошибках: что случилось и как это исправить по шагам.

Модуль не зависит от окон: им пользуются и ядро (проверка данных, расчет
материалов), и формы приложения.
"""

from psycopg2 import OperationalError

FIX_HEADER = "Как исправить:"
SERVICE_STEP = ("Откройте «Службы» Windows и проверьте, что служба "
                "PostgreSQL (postgresql-x64-18) запущена.")
SETTINGS_STEP = ("Проверьте переменные окружения: DB_PASSWORD — пароль "
                 "пользователя postgres, DB_NAME — имя базы (по умолчанию "
                 "partners_db).")
SCHEMA_STEP = ("Если база создавалась по старому скрипту, пересоздайте "
               "таблицы: выполните schema.sql, затем import.sql.")
REPORT_STEP = "Если ошибка повторится, передайте файл app.log разработчику."


def instructions(problem: str, *steps: str) -> str:
    """Текст окна ошибки: суть проблемы и пронумерованные шаги."""
    numbered = "\n".join(f"{number}. {step}"
                         for number, step in enumerate(steps, start=1))
    return f"{problem}\n\n{FIX_HEADER}\n{numbered}"


def first_line(error: Exception) -> str:
    """Первая строка текста ошибки: у psycopg2 он бывает многострочным."""
    lines = str(error).strip().splitlines()
    if not lines:
        return type(error).__name__
    return lines[0]


def database_message(action: str, error: Exception, retry_step: str) -> str:
    """Сообщение об ошибке базы с шагами под ее вид.

    OperationalError — нет связи с сервером: помогут служба и настройки
    подключения. Любая другая ошибка psycopg2 означает, что сервер
    ответил, но запрос не прошел, — чаще всего база создана старым
    скриптом и в ней не хватает таблиц или столбцов.
    """
    reason = first_line(error)
    if isinstance(error, OperationalError):
        return instructions(
            f"{action}: нет связи с базой данных.\n\nПричина: {reason}",
            SERVICE_STEP, SETTINGS_STEP, retry_step)
    return instructions(
        f"{action}: база данных ответила ошибкой.\n\nПричина: {reason}",
        SCHEMA_STEP, retry_step, REPORT_STEP)
