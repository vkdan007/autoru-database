-- Создание таблицы Make
CREATE TABLE Make (
    make_id SERIAL PRIMARY KEY,
    make_name VARCHAR(255) NOT NULL
);

-- Создание таблицы Auto
CREATE TABLE Auto (
    auto_id SERIAL PRIMARY KEY,
    make_id INT NOT NULL,
    year INT CHECK (year > 1885),
    color VARCHAR(50),
    mileage INT CHECK (mileage >= 0),
    FOREIGN KEY (make_id) REFERENCES Make (make_id)
);

-- Создание таблицы User
CREATE TABLE "User" (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

-- Создание таблицы UserAddress
CREATE TABLE UserAddress (
    user_address_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    address TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES "User" (user_id)
);

-- Создание таблицы Chat
CREATE TABLE Chat (
    chat_id SERIAL PRIMARY KEY
);

-- Создание таблицы Ad
CREATE TABLE Ad (
    ad_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    auto_id INT NOT NULL,
    user_address_id INT NOT NULL,
    publication_date DATE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES "User" (user_id),
    FOREIGN KEY (auto_id) REFERENCES Auto (auto_id),
    FOREIGN KEY (user_address_id) REFERENCES UserAddress (user_address_id)
);

-- Создание типа ENUM для статуса объявления (опционально)
CREATE TYPE ad_status AS ENUM ('open', 'close');

-- Создание таблицы AdInfo
CREATE TABLE AdInfo (
    ad_info_id SERIAL PRIMARY KEY,
    ad_id INT NOT NULL,
    description TEXT,
    photo_url TEXT,
    status ad_status NOT NULL, -- Использование ENUM
    price NUMERIC(10, 2) CHECK (price >= 0),
    FOREIGN KEY (ad_id) REFERENCES Ad (ad_id)
);

-- Создание таблицы Review
CREATE TABLE Review (
    review_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    ad_id INT NOT NULL,
    rating INT CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    date DATE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES "User" (user_id),
    FOREIGN KEY (ad_id) REFERENCES Ad (ad_id)
);

-- Создание таблицы UserChat
CREATE TABLE UserChat (
    user_id INT NOT NULL,
    chat_id INT NOT NULL,
    PRIMARY KEY (user_id, chat_id),
    FOREIGN KEY (user_id) REFERENCES "User" (user_id),
    FOREIGN KEY (chat_id) REFERENCES Chat (chat_id)
);

-- Создание таблицы Message
CREATE TABLE Message (
    message_id SERIAL PRIMARY KEY,
    chat_id INT NOT NULL,
    user_id INT NOT NULL,
    text TEXT,
    date TIMESTAMP NOT NULL,
    photo TEXT,
    FOREIGN KEY (chat_id) REFERENCES Chat (chat_id),
    FOREIGN KEY (user_id) REFERENCES "User" (user_id)
);
