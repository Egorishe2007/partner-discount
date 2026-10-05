"""Очистка «сырых» файлов заказчика и подготовка данных к импорту в базу.

python etl.py — читает data/*_raw.csv, пишет очищенные data/clean_*.csv,
журнал исправлений data/cleaning_log.csv и отклоненные строки
data/rejected_rows.csv.
"""

import csv
import datetime
import os
import re
from decimal import Decimal, InvalidOperation

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
PARTNERS_SOURCE = "partners_raw.csv"
PRODUCTS_SOURCE = "products_raw.csv"
SALES_SOURCE = "sales_history_raw.csv"
PARTNERS_TARGET = "clean_partners.csv"
PRODUCTS_TARGET = "clean_products.csv"
SALES_TARGET = "clean_sales_history.csv"
LOG_TARGET = "cleaning_log.csv"
REJECTED_TARGET = "rejected_rows.csv"

PARTNER_COLUMNS = ("id", "partner_type", "name", "inn", "email")
PRODUCT_COLUMNS = ("id", "name", "price")
SALE_COLUMNS = ("id", "partner_id", "product_id", "sale_date", "quantity",
                "amount")
LOG_COLUMNS = ("file", "line", "field", "before", "after")
REJECTED_COLUMNS = ("file", "line", "reason", "row")

LEGAL_FORMS = ("ООО", "ЗАО", "ОАО", "ПАО", "АО", "ИП")
# Дни идут первыми: так даты пишут в России, а 25.10.2023 и 28-10-2023 в
# файле только так и читаются.
DATE_FORMATS = ("%Y-%m-%d", "%d.%m.%Y", "%Y/%m/%d", "%d-%m-%Y",
                "%Y.%m.%d", "%d/%m/%Y")
# Латинские буквы, которые на экране не отличить от русских. Если их
# оставить, поиск по «Петров А.В.» не найдет партнера «Петров A.B.».
HOMOGLYPHS = str.maketrans("ABCEHKMOPTXaceopxy", "АВСЕНКМОРТХасеорху")
INITIALS = re.compile(r"^[A-Za-zА-Яа-яЁё]\.([A-Za-zА-Яа-яЁё]\.)?$")
LOOSE_DOTS = re.compile(r"\.{2,}")
INN_PATTERN = re.compile(r"^(\d{10}|\d{12})$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")
QUOTES = "\"'«»“”„"
MONEY_STEP = Decimal("0.01")


class RejectedRow(Exception):
    """Строку нельзя загрузить в базу: причина — в тексте исключения."""


class EtlReport:
    """Что ETL прочитал, исправил и отклонил — для журналов и итога."""

    def __init__(self):
        self.encodings = {}
        self.read = {}
        self.loaded = {}
        self.fixes = []
        self.rejected = []
        self.amount_mismatches = []

    def fix(self, file_name, line, field, before, after):
        """Записать исправление, если значение действительно изменилось."""
        if before != after:
            self.fixes.append((file_name, line, field, before, after))

    def reject(self, file_name, line, reason, row):
        """Записать строку, которая не пойдет в базу."""
        self.rejected.append((file_name, line, reason, ",".join(row)))


def read_csv(path: str):
    """Прочитать CSV и вернуть кодировку, заголовок и строки с номерами.

    Файлы заказчика пришли в разных кодировках: сначала пробуем UTF-8,
    а если байты в нее не укладываются — Windows-1251. Модуль csv, в
    отличие от COPY в PostgreSQL, не спотыкается о кавычку в середине
    значения вроде «Монитор 27"».
    """
    with open(path, "rb") as source:
        raw = source.read()
    try:
        text = raw.decode("utf-8-sig")
        encoding = "utf-8"
    except UnicodeDecodeError:
        text = raw.decode("cp1251")
        encoding = "cp1251"
    rows = list(csv.reader(text.splitlines()))
    numbered = [(number, row) for number, row in enumerate(rows[1:], start=2)
                if any(cell.strip() for cell in row)]
    return encoding, rows[0], numbered


def squeeze_spaces(value: str) -> str:
    """Убрать пробелы по краям и повторяющиеся пробелы внутри (TRIM)."""
    return " ".join(value.split())


def fix_initials(words: list) -> list:
    """Перевести латинские буквы в инициалах на русские: A.B. → А.В."""
    return [word.translate(HOMOGLYPHS) if INITIALS.match(word) else word
            for word in words]


def clean_partner_name(value: str):
    """Разделить «ООО "Вектор"» на форму собственности и название.

    Попутно убираются пробелы, кавычки по краям названия, лишние точки
    («...Петров») и латиница в инициалах.
    """
    text = squeeze_spaces(LOOSE_DOTS.sub(" ", value))
    words = text.split(" ")
    if words[0] not in LEGAL_FORMS:
        raise RejectedRow(f"не указана форма собственности: {value.strip()}")
    name = " ".join(fix_initials(words[1:])).strip(QUOTES + " ")
    if not name:
        raise RejectedRow("пустое наименование партнера")
    return words[0], name


def clean_inn(value: str) -> str:
    """ИНН из 10 или 12 цифр без пробелов."""
    inn = value.strip()
    if not INN_PATTERN.match(inn):
        raise RejectedRow(f"неверный ИНН: {value!r}")
    return inn


def clean_email(value: str) -> str:
    """Email без пробелов и в нижнем регистре: регистр в адресе не важен."""
    email = value.strip().lower()
    if not EMAIL_PATTERN.match(email):
        raise RejectedRow(f"неверный email: {value!r}")
    return email


def clean_date(value: str) -> str:
    """Дата в формате СУБД ГГГГ-ММ-ДД из любого формата файла."""
    text = value.strip()
    for date_format in DATE_FORMATS:
        try:
            parsed = datetime.datetime.strptime(text, date_format)
        except ValueError:
            continue
        return parsed.date().isoformat()
    raise RejectedRow(f"дата в неизвестном формате: {value!r}")


def clean_money(value: str) -> Decimal:
    """Денежная сумма с двумя знаками после запятой."""
    try:
        amount = Decimal(value.strip().replace(",", "."))
    except InvalidOperation:
        raise RejectedRow(f"сумма не число: {value!r}") from None
    if not amount.is_finite() or amount < 0:
        raise RejectedRow(f"неверная сумма: {value!r}")
    return amount.quantize(MONEY_STEP)


def clean_count(value: str) -> int:
    """Целое число больше нуля: идентификатор или количество."""
    text = value.strip()
    if not text.isdecimal() or int(text) == 0:
        raise RejectedRow(f"ожидалось целое число больше 0: {value!r}")
    return int(text)


def clean_partners(rows, report: EtlReport) -> list:
    """Очистить партнеров; повторный ИНН или email — отказ."""
    partners = []
    seen = set()
    for line, row in rows:
        try:
            raw_id, raw_name, raw_inn, raw_email = row
            partner_type, name = clean_partner_name(raw_name)
            partner = (clean_count(raw_id), partner_type, name,
                       clean_inn(raw_inn), clean_email(raw_email))
            for unique_value in (partner[3], partner[4]):
                if unique_value in seen:
                    raise RejectedRow(f"повтор уникального поля: "
                                      f"{unique_value}")
            seen.update((partner[3], partner[4]))
        except ValueError:
            report.reject(PARTNERS_SOURCE, line, "неверное число столбцов",
                          row)
            continue
        except RejectedRow as error:
            report.reject(PARTNERS_SOURCE, line, str(error), row)
            continue
        report.fix(PARTNERS_SOURCE, line, "partner_name", raw_name,
                   f"{partner_type} | {name}")
        report.fix(PARTNERS_SOURCE, line, "email", raw_email, partner[4])
        partners.append(partner)
    return partners


def clean_products(rows, report: EtlReport) -> list:
    """Очистить справочник номенклатуры."""
    products = []
    for line, row in rows:
        try:
            raw_id, raw_name, raw_price = row
            name = squeeze_spaces(raw_name)
            if not name:
                raise RejectedRow("пустое наименование продукции")
            product = (clean_count(raw_id), name, clean_money(raw_price))
        except ValueError:
            report.reject(PRODUCTS_SOURCE, line, "неверное число столбцов",
                          row)
            continue
        except RejectedRow as error:
            report.reject(PRODUCTS_SOURCE, line, str(error), row)
            continue
        report.fix(PRODUCTS_SOURCE, line, "product_name", raw_name, name)
        products.append(product)
    return products


def clean_sales(rows, partner_ids, products, report: EtlReport) -> list:
    """Очистить продажи и отбросить ссылки на несуществующие записи.

    Внешний ключ проверяется до загрузки: строка с партнером, которого
    нет в справочнике, не пройдет ограничение FOREIGN KEY, и тогда не
    загрузился бы весь файл, а не одна битая строка.
    """
    prices = {product[0]: product[2] for product in products}
    sales = []
    for line, row in rows:
        try:
            (raw_id, raw_partner, raw_product, raw_date, raw_quantity,
             raw_amount) = row
            sale = (clean_count(raw_id), clean_count(raw_partner),
                    clean_count(raw_product), clean_date(raw_date),
                    clean_count(raw_quantity), clean_money(raw_amount))
            if sale[1] not in partner_ids:
                raise RejectedRow(f"партнер {sale[1]} не найден")
            if sale[2] not in prices:
                raise RejectedRow(f"продукция {sale[2]} не найдена")
        except ValueError:
            report.reject(SALES_SOURCE, line, "неверное число столбцов", row)
            continue
        except RejectedRow as error:
            report.reject(SALES_SOURCE, line, str(error), row)
            continue
        report.fix(SALES_SOURCE, line, "sale_date", raw_date, sale[3])
        if sale[5] != prices[sale[2]] * sale[4]:
            report.amount_mismatches.append((sale[0], sale[5]))
        sales.append(sale)
    return sales


def write_csv(path: str, columns, rows):
    """Записать CSV в UTF-8; кавычки внутри значений экранирует csv."""
    with open(path, "w", encoding="utf-8", newline="") as target:
        writer = csv.writer(target)
        writer.writerow(columns)
        writer.writerows(rows)


def run_etl(data_dir: str = DATA_DIR) -> EtlReport:
    """Прочитать сырые файлы, очистить и записать результат в data_dir."""
    report = EtlReport()
    sources = {}
    for name in (PARTNERS_SOURCE, PRODUCTS_SOURCE, SALES_SOURCE):
        encoding, header, rows = read_csv(os.path.join(data_dir, name))
        report.encodings[name] = encoding
        report.read[name] = len(rows)
        sources[name] = rows
    partners = clean_partners(sources[PARTNERS_SOURCE], report)
    products = clean_products(sources[PRODUCTS_SOURCE], report)
    partner_ids = {partner[0] for partner in partners}
    sales = clean_sales(sources[SALES_SOURCE], partner_ids, products,
                        report)
    report.loaded = {PARTNERS_SOURCE: len(partners),
                     PRODUCTS_SOURCE: len(products),
                     SALES_SOURCE: len(sales)}
    write_csv(os.path.join(data_dir, PARTNERS_TARGET), PARTNER_COLUMNS,
              partners)
    write_csv(os.path.join(data_dir, PRODUCTS_TARGET), PRODUCT_COLUMNS,
              products)
    write_csv(os.path.join(data_dir, SALES_TARGET), SALE_COLUMNS, sales)
    write_csv(os.path.join(data_dir, LOG_TARGET), LOG_COLUMNS, report.fixes)
    write_csv(os.path.join(data_dir, REJECTED_TARGET), REJECTED_COLUMNS,
              report.rejected)
    return report


def print_report(report: EtlReport):
    """Итог очистки для консоли."""
    for name, count in report.read.items():
        print(f"{name}: кодировка {report.encodings[name]}, строк {count}, "
              f"загружено {report.loaded[name]}, "
              f"отклонено {count - report.loaded[name]}")
    print(f"Исправлено значений: {len(report.fixes)} "
          f"(подробно — data/{LOG_TARGET})")
    for file_name, line, reason, row in report.rejected:
        print(f"Отклонено: {file_name}, строка {line}: {reason}")
    if report.amount_mismatches:
        print(f"Сумма не равна цене × количество: "
              f"{report.amount_mismatches}")
    else:
        print("Суммы всех продаж совпадают с ценой × количество.")


def main():
    print_report(run_etl())


if __name__ == "__main__":
    main()
