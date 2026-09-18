# Интеграция с БД и агрегация данных (SQL + Backend)

Суммарный объем продаж партнера берется из базы данных запросом с
группировкой, а процент скидки считает функция из первого задания.
На выходе — словарь с данными партнера и его текущей скидкой.

## Файлы

| Файл | Назначение |
| --- | --- |
| `db.py` | подключение к PostgreSQL через native-драйвер psycopg2 |
| `partner_service.py` | SQL-запрос с `SUM(quantity)` и `LEFT JOIN`, расчет скидки |
| `partner_discount.py` | функция расчета скидки из задания 1, без изменений |
| `main.py` | консольная проверка |
| `schema.sql` | таблицы `partners`, `sales_history` и тестовые данные |

## Подготовка базы данных

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

## Запуск

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
