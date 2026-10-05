-- Проверка импорта: что загрузилось и не осталось ли аномалий.
-- Запуск: psql -U postgres -d partners_db -f import_check.sql

-- 1. Сколько строк в каждой таблице: 5 партнеров, 3 товара, 5 продаж.
SELECT 'partners' AS table_name, COUNT(*) AS row_count FROM partners
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'sales_history', COUNT(*) FROM sales_history;

-- 2. Лишних пробелов не осталось: TRIM ничего не меняет, двойных нет.
SELECT COUNT(*) AS values_with_extra_spaces
FROM (
    SELECT name AS value FROM partners
    UNION ALL
    SELECT email FROM partners
    UNION ALL
    SELECT name FROM products
) AS text_values
WHERE value <> TRIM(value) OR value LIKE '%  %';

-- 3. Даты продаж — в формате СУБД ГГГГ-ММ-ДД.
SELECT id, to_char(sale_date, 'YYYY-MM-DD') AS sale_date
FROM sales_history
ORDER BY id;

-- 4. Нет продаж, ссылающихся на несуществующих партнеров или товары.
SELECT COUNT(*) AS broken_links
FROM sales_history AS s
LEFT JOIN partners AS p ON p.id = s.partner_id
LEFT JOIN products AS pr ON pr.id = s.product_id
WHERE p.id IS NULL OR pr.id IS NULL;

-- 5. Сумма каждой продажи совпадает с ценой справочника × количество.
SELECT s.id, s.amount, pr.price * s.quantity AS expected_amount
FROM sales_history AS s
JOIN products AS pr ON pr.id = s.product_id
WHERE s.amount <> pr.price * s.quantity;
