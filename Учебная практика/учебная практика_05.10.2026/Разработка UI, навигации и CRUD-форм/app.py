"""Точка входа приложения: запуск CRM со списком партнеров."""

from app_log import get_logger, setup_logging
from navigation import Navigator

logger = get_logger("app")


def main():
    setup_logging()
    logger.info("Приложение запущено")
    Navigator().start()
    logger.info("Приложение закрыто")


if __name__ == "__main__":
    main()
