-- Импорт очищенных данных в PostgreSQL.
-- Запуск из папки задания: psql -U postgres -d partners_db -f import.sql
-- Пути в \copy указаны относительно папки, из которой запущен psql.

SET client_encoding = 'UTF8';

\copy partners (id, partner_type, name, inn, email) FROM 'data/clean_partners.csv' WITH (FORMAT csv, HEADER true)
\copy products (id, name, price) FROM 'data/clean_products.csv' WITH (FORMAT csv, HEADER true)
\copy sales_history (id, partner_id, product_id, sale_date, quantity, amount) FROM 'data/clean_sales_history.csv' WITH (FORMAT csv, HEADER true)

-- Номера записей пришли из файлов, поэтому счетчики нужно сдвинуть:
-- иначе следующий партнер, добавленный из приложения, получит id = 1,
-- который уже занят.
SELECT setval(pg_get_serial_sequence('partners', 'id'), MAX(id))
FROM partners;

SELECT setval(pg_get_serial_sequence('products', 'id'), MAX(id))
FROM products;

SELECT setval(pg_get_serial_sequence('sales_history', 'id'), MAX(id))
FROM sales_history;
