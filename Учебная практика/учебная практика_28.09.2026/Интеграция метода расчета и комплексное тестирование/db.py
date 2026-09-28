"""Подключение к PostgreSQL через native-драйвер psycopg2."""

import os

import psycopg2


def get_connection():
    """Открыть соединение; параметры берутся из переменных окружения.

    Пароль задается в DB_PASSWORD (или стандартной PGPASSWORD),
    в коде он не хранится.
    """
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "partners_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD"),
    )
