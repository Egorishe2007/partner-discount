# Расчет скидки партнера

Учебный проект: ядро бизнес-логики (индивидуальный процент скидки партнера)
и получение суммарного объема продаж партнера из базы данных.

Python 3.10, PostgreSQL 18, драйвер psycopg2.

## Состав проекта

| Файл | Назначение |
| --- | --- |
| `partner_discount.py` | Задание 1: функция `calculate_partner_discount` |
| `test_partner_discount.py` | Задание 1: unit-тесты граничных значений |
| `db.py` | Задание 2: подключение к PostgreSQL через psycopg2 |
| `partner_service.py` | Задание 2: SQL-запрос (`SUM` + `LEFT JOIN`) и расчет скидки |
| `main.py` | Задание 2: консольная проверка |
| `schema.sql` | Задание 2: таблицы `partners`, `sales_history` и тестовые данные |

## Задание 1. Ядро бизнес-логики (расчет скидки)

Критерии расчета из ТЗ:

| Суммарный объем продукции | Скидка |
| --- | --- |
| менее 10 000 ед. | 0 % |
| от 10 000 до 49 999 ед. | 5 % |
| от 50 000 до 299 999 ед. | 10 % |
| от 300 000 ед. и более | 15 % |

Отрицательный объем считается ошибкой ввода: функция выдает `ValueError`.

Запуск тестов:

```
python -m unittest -v
```

Проверяются границы 0, 9999, 10000, 49999, 50000, 299999, 300000 и
отрицательное значение — всего 8 тестов.

Покрытие тестами:

```
pip install coverage
python -m coverage run --branch -m unittest
python -m coverage report -m
```

```
Name                       Stmts   Miss Branch BrPart  Cover   Missing
----------------------------------------------------------------------
partner_discount.py           10      0      8      0   100%
test_partner_discount.py      20      0      0      0   100%
----------------------------------------------------------------------
TOTAL                         30      0      8      0   100%
```

## Задание 2. Интеграция с БД и агрегация данных

Подготовка базы данных:

```
psql -U postgres -c "CREATE DATABASE partners_db"
psql -U postgres -d partners_db -f schema.sql
```

Параметры подключения берутся из переменных окружения, пароль в коде не
хранится:

| Переменная | Значение по умолчанию |
| --- | --- |
| `DB_HOST` | `localhost` |
| `DB_PORT` | `5432` |
| `DB_NAME` | `partners_db` |
| `DB_USER` | `postgres` |
| `DB_PASSWORD` | не задан, берется стандартная `PGPASSWORD` |

Установка драйвера и запуск:

```
pip install -r requirements.txt
python main.py
```

Вывод на тестовых данных из `schema.sql`:

```
{'id': 1, 'partner_type': 'ООО', 'name': 'СтройМастер', 'director': 'Иванов Иван Иванович', 'email': 'info@stroymaster.example', 'phone': '+7 900 000 00 01', 'rating': 7, 'total_quantity': 9999, 'discount_percent': 0}
{'id': 2, 'partner_type': 'ЗАО', 'name': 'Паркет-Сервис', 'director': 'Петров Петр Петрович', 'email': 'sales@parket.example', 'phone': '+7 900 000 00 02', 'rating': 5, 'total_quantity': 10000, 'discount_percent': 5}
{'id': 3, 'partner_type': 'ООО', 'name': 'Дом и Интерьер', 'director': 'Сидорова Анна Сергеевна', 'email': 'office@dom-interier.example', 'phone': '+7 900 000 00 03', 'rating': 9, 'total_quantity': 49999, 'discount_percent': 5}
{'id': 4, 'partner_type': 'ПАО', 'name': 'ОтделкаПро', 'director': 'Кузнецов Олег Викторович', 'email': 'partner@otdelka.example', 'phone': '+7 900 000 00 04', 'rating': 8, 'total_quantity': 50000, 'discount_percent': 10}
{'id': 5, 'partner_type': 'ОАО', 'name': 'Большой Склад', 'director': 'Смирнова Елена Андреевна', 'email': 'zakaz@sklad.example', 'phone': '+7 900 000 00 05', 'rating': 10, 'total_quantity': 300000, 'discount_percent': 15}
{'id': 6, 'partner_type': 'ООО', 'name': 'Новый Партнер', 'director': 'Васильев Дмитрий Игоревич', 'email': 'hello@new-partner.example', 'phone': '+7 900 000 00 06', 'rating': 3, 'total_quantity': 0, 'discount_percent': 0}
```

`LEFT JOIN` нужен, чтобы в результат попадал и партнер без продаж: у
партнера «Новый Партнер» продаж нет, и `COALESCE` заменяет его пустую
сумму (`NULL`) на 0. Для несуществующего партнера функция возвращает
`None`.
