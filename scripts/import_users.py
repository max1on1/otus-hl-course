import os
import uuid
import io
import csv
import math
from dotenv import load_dotenv
from faker import Faker
import bcrypt
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

# Загрузка настроек из .env
load_dotenv()
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "socialnetwork")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_URL = f"dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD} host={DB_HOST} port={DB_PORT}"

# Параметры
NUM_USERS = 10000
BATCH_SIZE = 1000
NUM_BATCHES = math.ceil(NUM_USERS / BATCH_SIZE)
NUM_PROCESSES = 4   # для генерации и хеширования (CPU-bound)
NUM_THREADS = 8     # для заливки в БД (I/O-bound)

# Инициализация Faker и bcrypt
fake = Faker()
# Для тестовых данных устанавливаем меньший cost
SALT = bcrypt.gensalt(rounds=10)
# Пред-хешированный пароль для всех тестовых пользователей
PASSWORD_HASH = bcrypt.hashpw(b"password123", SALT).decode()

# Создаём пул соединений
pool = ThreadedConnectionPool(minconn=1, maxconn=NUM_THREADS, dsn=DB_URL)

INSERT_COLUMNS = (
    'id', 'first_name', 'second_name', 'birthdate',
    'biography', 'city', 'password_hash'
)


def generate_batch(_batch_index):
    """
    Генерирует один батч тестовых пользователей.
    Возвращает список кортежей-строк.
    """
    batch = []
    for _ in range(BATCH_SIZE):
        user_id = str(uuid.uuid4())
        first_name = fake.first_name()
        second_name = fake.last_name()
        birthdate = fake.date_of_birth().strftime("%Y-%m-%d")
        biography = fake.text(max_nb_chars=200)
        city = fake.city()
        password_hash = PASSWORD_HASH
        batch.append((user_id, first_name, second_name, birthdate,
                      biography, city, password_hash))
    return batch


def insert_batch_copy(batch_info):
    """
    Получает кортеж (batch_number, batch_list) и копирует данные в БД через COPY.
    """
    batch_number, batch = batch_info
    conn = pool.getconn()
    try:
        cur = conn.cursor()
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        # Запись строк в буфер как CSV, с экранированием
        writer.writerows(batch)
        buffer.seek(0)
        # COPY FROM STDIN WITH CSV автоматически парсит кавычки и экранирование
        cur.copy_expert(
            sql=f"COPY users ({', '.join(INSERT_COLUMNS)}) FROM STDIN WITH CSV",
            file=buffer
        )
        conn.commit()
        cur.close()
        print(f"Batch {batch_number} inserted.")
    finally:
        pool.putconn(conn)


def main():
    print("Start generating batches...")
    # 1) Генерируем все батчи параллельно (CPU-bound)
    with ProcessPoolExecutor(max_workers=NUM_PROCESSES) as proc:
        all_batches = list(proc.map(generate_batch, range(NUM_BATCHES)))

    print("Start inserting batches into DB...")
    # Подготавливаем аргументы для потоков
    batch_args = list(enumerate(all_batches, start=1))
    # 2) Заливаем батчи параллельно (I/O-bound)
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as threads:
        threads.map(insert_batch_copy, batch_args)

    # Закрываем пул соединений
    pool.closeall()
    print("All users inserted successfully!")


if __name__ == '__main__':
    main()
