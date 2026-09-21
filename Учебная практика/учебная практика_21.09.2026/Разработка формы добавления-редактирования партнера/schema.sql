-- Таблицы и тестовые данные для задания «Интеграция с БД».
-- Объемы продаж подобраны под границы скидок из подзадания 1,
-- у последнего партнера продаж нет (проверка LEFT JOIN).

SET client_encoding = 'UTF8';

CREATE TABLE partners (
    id            SERIAL       PRIMARY KEY,
    partner_type  VARCHAR(10)  NOT NULL,
    name          VARCHAR(255) NOT NULL UNIQUE,
    director      VARCHAR(255) NOT NULL,
    email         VARCHAR(255) NOT NULL,
    phone         VARCHAR(20)  NOT NULL,
    legal_address VARCHAR(500) NOT NULL,
    inn           VARCHAR(12)  NOT NULL UNIQUE,
    rating        INTEGER      NOT NULL CHECK (rating >= 0)
);

CREATE TABLE sales_history (
    id           SERIAL       PRIMARY KEY,
    partner_id   INTEGER      NOT NULL REFERENCES partners (id),
    product_name VARCHAR(255) NOT NULL,
    quantity     INTEGER      NOT NULL CHECK (quantity > 0),
    sale_date    DATE         NOT NULL
);

CREATE INDEX idx_sales_history_partner_id ON sales_history (partner_id);

INSERT INTO partners
    (partner_type, name, director, email, phone, legal_address, inn, rating)
VALUES
    ('ООО', 'СтройМастер', 'Иванов Иван Иванович',
     'info@stroymaster.example', '+7 900 000 00 01',
     'г. Москва, ул. Строителей, д. 1', '7700000001', 7),
    ('ЗАО', 'Паркет-Сервис', 'Петров Петр Петрович',
     'sales@parket.example', '+7 900 000 00 02',
     'г. Казань, ул. Лесная, д. 5', '1600000002', 5),
    ('ООО', 'Дом и Интерьер', 'Сидорова Анна Сергеевна',
     'office@dom-interier.example', '+7 900 000 00 03',
     'г. Самара, пр. Мира, д. 12', '6300000003', 9),
    ('ПАО', 'ОтделкаПро', 'Кузнецов Олег Викторович',
     'partner@otdelka.example', '+7 900 000 00 04',
     'г. Пермь, ул. Заводская, д. 8', '5900000004', 8),
    ('ОАО', 'Большой Склад', 'Смирнова Елена Андреевна',
     'zakaz@sklad.example', '+7 900 000 00 05',
     'г. Тула, ул. Складская, д. 3', '7100000005', 10),
    ('ООО', 'Новый Партнер', 'Васильев Дмитрий Игоревич',
     'hello@new-partner.example', '+7 900 000 00 06',
     'г. Омск, ул. Новая, д. 1', '5500000006', 3);

INSERT INTO sales_history (partner_id, product_name, quantity, sale_date)
VALUES
    (1, 'Паркетная доска', 5000, '2025-03-15'),
    (1, 'Ламинат', 4999, '2025-06-10'),
    (2, 'Паркетная доска', 7000, '2025-02-01'),
    (2, 'Пробковое покрытие', 3000, '2025-09-20'),
    (3, 'Ламинат', 30000, '2025-04-05'),
    (3, 'Паркетная доска', 19999, '2026-01-12'),
    (4, 'Ламинат', 20000, '2025-05-18'),
    (4, 'Паркетная доска', 20000, '2025-11-03'),
    (4, 'Пробковое покрытие', 10000, '2026-02-27'),
    (5, 'Паркетная доска', 150000, '2025-07-07'),
    (5, 'Ламинат', 150000, '2026-03-14');
