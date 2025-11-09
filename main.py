import psycopg2
from psycopg2.extras import execute_values
from faker import Faker
import random
from tqdm import tqdm
from datetime import datetime, timedelta

# Инициализация Faker
fake = Faker('ru_RU')

# Параметры подключения к базе данных
DB_PARAMS = {
    'dbname': 'autoru',
    'user': 'postgres',
    'password': '3547',
    'host': 'localhost',
    'port': '5432',
}

# Подключение к базе данных PostgreSQL
conn = psycopg2.connect(**DB_PARAMS)
conn.autocommit = False  # Включаем транзакции
cursor = conn.cursor()

# Список фиксированных названий марок автомобилей
FIXED_MAKES = [
    "Toyota",
    "Ford",
    "Volkswagen",
    "Honda",
    "Chevrolet",
    "BMW",
    "Mercedes-Benz",
    "Audi",
    "Nissan",
    "Hyundai",
    "Kia",
    "Subaru",
    "Lexus",
    "Mazda",
    "Jaguar",
    "Land Rover",
    "Tesla",
    "Fiat",
    "Peugeot",
    "Renault"
]

# Список допустимых цветов автомобилей
CAR_COLORS = [
    "Black", "White", "Red", "Blue", "Silver", "Grey", "Green",
    "Yellow", "Brown", "Orange", "Purple", "Gold", "Beige",
    "Maroon", "Cyan", "Magenta", "Turquoise", "Pink", "Lavender", "Navy Blue"
]


# Функции генерации данных

def generate_makes():
    """
    Возвращает список кортежей с названиями марок для вставки в таблицу Make.
    """
    makes = [(make,) for make in FIXED_MAKES]
    return makes


def generate_users(n):
    """
    Генерирует список пользователей.
    """
    users = []
    for _ in range(n):
        username = fake.user_name()[:255]  # Ограничиваем длину до 255 символов
        email = fake.user_name()[:50] + fake.unique.email()[:205]  # Ограничиваем длину до 255 символов
        password = fake.password(length=12)[:255]  # Ограничиваем длину до 255 символов
        users.append((username, email, password))
    return users


def generate_user_addresses(user_ids, n_per_user=2):
    """
    Генерирует адреса для пользователей.
    """
    user_addresses = []
    for user_id in user_ids:
        for _ in range(n_per_user):
            address = fake.address().replace('\n', ', ')[:1000]  # Ограничиваем длину до 1000 символов
            user_addresses.append((user_id, address))
    return user_addresses


def generate_autos(make_ids, n):
    """
    Генерирует автомобили.
    """
    autos = []
    for _ in range(n):
        make_id = random.choice(make_ids)
        year = random.randint(1980, datetime.now().year)  # Год выпуска от 1980 до текущего года
        color = random.choice(CAR_COLORS)  # Выбираем цвет из предопределённого списка
        mileage = random.randint(0, 300000)
        autos.append((make_id, year, color, mileage))
    return autos


def generate_ads(user_ads_mapping, auto_ids, user_address_ids, auto_year_mapping):
    """
    Генерирует объявления для пользователей, обеспечивая корректные даты публикации.
    """
    ads = []
    for user_id, num_ads in user_ads_mapping.items():
        for _ in range(num_ads):
            auto_id = random.choice(auto_ids)
            user_address_id = random.choice(user_address_ids)
            car_year = auto_year_mapping.get(auto_id, 1980)  # По умолчанию 1980, если авто не найдено
            # Публикация объявления должна быть после года выпуска автомобиля
            # Генерируем дату между 1 января года выпуска и сегодняшним днём
            try:
                start_date = datetime(car_year, 1, 1)
            except ValueError:
                start_date = datetime(1980, 1, 1)  # Корректировка некорректных дат
            end_date = datetime.now()
            if start_date > end_date:
                start_date = end_date - timedelta(days=365)
            publication_date = fake.date_between(start_date=start_date, end_date='today')
            ads.append((user_id, auto_id, user_address_id, publication_date))
    return ads


def generate_ad_info(ad_ids):
    """
    Генерирует информацию об объявлениях.
    """
    ad_infos = []
    for ad_id in ad_ids:
        description = fake.text(max_nb_chars=200)[:200]  # Ограничиваем длину до 200 символов
        photo_url = fake.image_url()[:255] if random.random() < 0.5 else None  # 50% с фото
        status = random.choice(['open', 'close'])  # Только 'open' или 'close'
        price = round(random.uniform(500, 100000), 2)
        ad_infos.append((ad_id, description, photo_url, status, price))
    return ad_infos


def generate_reviews(user_reviews_mapping, ad_ids):
    """
    Генерирует отзывы от пользователей.
    """
    reviews = []
    for user_id, num_reviews in user_reviews_mapping.items():
        for _ in range(num_reviews):
            if not ad_ids:
                break  # Нет объявлений для отзывов
            ad_id = random.choice(ad_ids)
            rating = random.randint(1, 5)
            comment = fake.sentence(nb_words=12)[:1000]  # Ограничиваем длину до 1000 символов
            date = fake.date_between(start_date='-1y', end_date='today')
            reviews.append((user_id, ad_id, rating, comment, date))
    return reviews


def generate_chats(user_chats_mapping, user_ids):
    """
    Генерирует чаты и связи пользователей с чатами.
    """
    user_chats = set()
    chat_members = {}  # Словарь: chat_id -> set(user_id)

    for user_id, chat_count in user_chats_mapping.items():
        for _ in range(chat_count):
            # Определяем, присоединяться ли к существующему чату или создать новый
            if chat_members and random.random() < 0.7:
                # Присоединяемся к случайному существующему чату
                chat_id = random.choice(list(chat_members.keys()))
            else:
                # Создаём новый чат
                insert_query = """
                    INSERT INTO Chat DEFAULT VALUES RETURNING chat_id;
                """
                cursor.execute(insert_query)
                chat_id = cursor.fetchone()[0]
                chat_members[chat_id] = set()

            # Добавляем пользователя в чат
            if user_id not in chat_members[chat_id]:
                chat_members[chat_id].add(user_id)
                user_chats.add((user_id, chat_id))

                # Если чат имеет менее 2 участников, добавляем ещё одного случайного пользователя
                if len(chat_members[chat_id]) == 1:
                    other_user_id = random.choice(user_ids)
                    while other_user_id == user_id:
                        other_user_id = random.choice(user_ids)
                    chat_members[chat_id].add(other_user_id)
                    user_chats.add((other_user_id, chat_id))

    return list(user_chats)


def generate_messages(chat_ids, user_ids, n):
    """
    Генерирует сообщения в чатах.
    """
    messages = []
    for _ in range(n):
        if not chat_ids:
            break  # Нет чатов для сообщений
        chat_id = random.choice(chat_ids)
        # Получаем участников чата
        cursor.execute("""
            SELECT user_id FROM UserChat WHERE chat_id = %s;
        """, (chat_id,))
        chat_users = cursor.fetchall()
        if not chat_users:
            continue  # Если в чате нет участников, пропускаем
        user_id = random.choice(chat_users)[0]
        text = fake.text(max_nb_chars=200)[:200]  # Ограничиваем длину до 200 символов
        date = fake.date_time_between(start_date='-1y', end_date='now')
        photo = fake.image_url()[:255] if random.random() < 0.3 else None  # 30% с фото
        messages.append((chat_id, user_id, text, date, photo))
    return messages


# Функции вставки данных

def insert_makes(makes):
    """
    Вставляет записи в таблицу Make и возвращает список make_id.
    """
    insert_query = """
        INSERT INTO Make (make_name) VALUES %s RETURNING make_id;
    """
    execute_values(cursor, insert_query, makes, template=None, page_size=100)
    make_ids = [row[0] for row in cursor.fetchall()]
    return make_ids


def insert_users(users):
    """
    Вставляет записи в таблицу User и возвращает список user_id.
    """
    insert_query = """
        INSERT INTO "User" (username, email, password) VALUES %s RETURNING user_id;
    """
    execute_values(cursor, insert_query, users, template=None, page_size=100)
    user_ids = [row[0] for row in cursor.fetchall()]
    return user_ids


def insert_user_addresses(user_addresses):
    """
    Вставляет записи в таблицу UserAddress и возвращает список user_address_id.
    """
    insert_query = """
        INSERT INTO UserAddress (user_id, address) VALUES %s RETURNING user_address_id;
    """
    execute_values(cursor, insert_query, user_addresses, template=None, page_size=100)
    user_address_ids = [row[0] for row in cursor.fetchall()]
    return user_address_ids


def insert_autos(autos):
    """
    Вставляет записи в таблицу Auto и возвращает список auto_id.
    """
    insert_query = """
        INSERT INTO Auto (make_id, year, color, mileage) VALUES %s RETURNING auto_id;
    """
    execute_values(cursor, insert_query, autos, template=None, page_size=100)
    auto_ids = [row[0] for row in cursor.fetchall()]
    return auto_ids


def insert_ads(ads):
    """
    Вставляет записи в таблицу Ad и возвращает список ad_id.
    """
    insert_query = """
        INSERT INTO Ad (user_id, auto_id, user_address_id, publication_date) 
        VALUES %s RETURNING ad_id;
    """
    execute_values(cursor, insert_query, ads, template=None, page_size=100)
    ad_ids = [row[0] for row in cursor.fetchall()]
    return ad_ids


def insert_ad_infos(ad_infos):
    """
    Вставляет записи в таблицу AdInfo и возвращает список ad_info_id.
    """
    insert_query = """
        INSERT INTO AdInfo (ad_id, description, photo_url, status, price) 
        VALUES %s RETURNING ad_info_id;
    """
    execute_values(cursor, insert_query, ad_infos, template=None, page_size=100)
    ad_info_ids = [row[0] for row in cursor.fetchall()]
    return ad_info_ids


def insert_reviews(reviews):
    """
    Вставляет записи в таблицу Review и возвращает список review_id.
    """
    insert_query = """
        INSERT INTO Review (user_id, ad_id, rating, comment, date) 
        VALUES %s RETURNING review_id;
    """
    execute_values(cursor, insert_query, reviews, template=None, page_size=100)
    review_ids = [row[0] for row in cursor.fetchall()]
    return review_ids


def insert_user_chats(user_chats):
    """
    Вставляет записи в таблицу UserChat. Использует ON CONFLICT DO NOTHING для предотвращения дублирования.
    """
    insert_query = """
        INSERT INTO UserChat (user_id, chat_id) VALUES %s ON CONFLICT DO NOTHING;
    """
    execute_values(cursor, insert_query, user_chats, template=None, page_size=100)


def insert_messages(messages):
    """
    Вставляет записи в таблицу Message и возвращает список message_id.
    """
    insert_query = """
        INSERT INTO Message (chat_id, user_id, text, date, photo) 
        VALUES %s RETURNING message_id;
    """
    execute_values(cursor, insert_query, messages, template=None, page_size=100)
    message_ids = [row[0] for row in cursor.fetchall()]
    return message_ids


# Основная функция

def main():
    try:
        # Параметры генерации
        NUM_USERS = 5000
        ADDRESSES_PER_USER = 2
        NUM_AUTOS = 7000
        # Для объявлений и отзывов будем генерировать случайные количества
        MAX_ADS_PER_USER = 10
        MAX_REVIEWS_PER_USER = 10
        # Для чатов
        MAX_CHATS_PER_USER = 5
        NUM_MESSAGES = 300

        # 1. Вставка Make
        print("Генерация и вставка Make...")
        makes = generate_makes()
        make_ids = insert_makes(makes)
        print(f"Вставлено {len(make_ids)} марок автомобилей.")
        conn.commit()

        # 2. Вставка Users
        print("Генерация и вставка Users...")
        users = generate_users(NUM_USERS)
        user_ids = insert_users(users)
        print(f"Вставлено {len(user_ids)} пользователей.")
        conn.commit()

        # 3. Вставка User Addresses
        print("Генерация и вставка User Addresses...")
        user_addresses = generate_user_addresses(user_ids, ADDRESSES_PER_USER)
        user_address_ids = insert_user_addresses(user_addresses)
        print(f"Вставлено {len(user_address_ids)} адресов пользователей.")
        conn.commit()

        # 4. Вставка Autos
        print("Генерация и вставка Autos...")
        autos = generate_autos(make_ids, NUM_AUTOS)
        auto_ids = insert_autos(autos)
        print(f"Вставлено {len(auto_ids)} автомобилей.")
        conn.commit()

        # Создаём mapping auto_id -> year для использования при генерации объявлений
        cursor.execute("SELECT auto_id, year FROM Auto;")
        auto_year_mapping = {row[0]: row[1] for row in cursor.fetchall()}

        # 5. Генерация и Вставка Ads
        print("Генерация и вставка Ads...")
        # Создаём mapping user_id -> number_of_ads
        user_ads_mapping = {user_id: random.randint(0, MAX_ADS_PER_USER) for user_id in user_ids}
        ads = generate_ads(user_ads_mapping, auto_ids, user_address_ids, auto_year_mapping)
        ad_ids = insert_ads(ads)
        print(f"Вставлено {len(ad_ids)} объявлений.")
        conn.commit()

        # 6. Генерация и Вставка AdInfo
        print("Генерация и вставка AdInfo...")
        ad_infos = generate_ad_info(ad_ids)
        ad_info_ids = insert_ad_infos(ad_infos)
        print(f"Вставлено {len(ad_info_ids)} записей AdInfo.")
        conn.commit()

        # 7. Генерация и Вставка Reviews
        print("Генерация и вставка Reviews...")
        # Создаём mapping user_id -> number_of_reviews
        user_reviews_mapping = {user_id: random.randint(0, MAX_REVIEWS_PER_USER) for user_id in user_ids}
        reviews = generate_reviews(user_reviews_mapping, ad_ids)
        review_ids = insert_reviews(reviews)
        print(f"Вставлено {len(review_ids)} отзывов.")
        conn.commit()

        # 8. Генерация и Вставка Chats и UserChats
        print("Генерация и вставка Chats и UserChats...")
        # Создаём mapping user_id -> number_of_chats
        user_chats_mapping = {user_id: random.randint(0, MAX_CHATS_PER_USER) for user_id in user_ids}
        user_chats = generate_chats(user_chats_mapping, user_ids)
        insert_user_chats(user_chats)
        print(f"Вставлено {len(user_chats)} записей UserChat.")
        conn.commit()

        # Получаем список уникальных chat_id из UserChat
        cursor.execute("SELECT DISTINCT chat_id FROM UserChat;")
        chat_ids = [row[0] for row in cursor.fetchall()]
        print(f"Обнаружено {len(chat_ids)} чатов.")

        # 9. Генерация и Вставка Messages
        print("Генерация и вставка Messages...")
        messages = generate_messages(chat_ids, user_ids, NUM_MESSAGES)
        message_ids = insert_messages(messages)
        print(f"Вставлено {len(message_ids)} сообщений.")
        conn.commit()

        print("Заполнение данных завершено успешно.")

    except Exception as e:
        conn.rollback()
        print(f"Произошла ошибка: {e}")

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
