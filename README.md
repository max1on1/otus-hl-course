# Что есть в проекте
- Backend на **FastAPI**
- База данных **PostgreSQL** с репликацией
- Подключение к БД через `asyncpg`
- Кеширование ленты друзей в **Redis**
- Обмен сообщениями через **RabbitMQ**
- Контейнеризация при помощи **Docker Compose**
- Чистые SQL‑миграции
- Готовая коллекция запросов для **Postman**

## Как запустить проект

Клонируем репозиторий:

```
git clone https://github.com/max1on1/otus-hl-course.git
cd otus-hl-course
```

Запустить docker compose:

```
docker-compose up --build
```

Таблица в ДБ создается автоматически

### После запуска будут доступны сервисы:

Backend API (FastAPI)
http://localhost:8000

PostgreSQL
localhost:5432 (user: postgres, pass: postgres, db: socialnetwork)

### Postman Collection

1. Из папке postman необходимо экспортировать postman_collection и postman_environment
2. Запустить коллекцию
3. ???
4. Profit

### Структура проекта
```
├── app                  # исходный код приложения
│   ├── handlers.py      # обработчики HTTP
│   ├── models.py        # Pydantic-модели
│   ├── db.py            # работа с PostgreSQL
│   ├── cache.py         # Redis-кеширование
│   ├── dialogs.py       # диалоги пользователей
│   ├── mq.py            # работа с RabbitMQ
│   └── Dockerfile       # образ приложения
├── docker-compose.yml   # инфраструктура проекта
├── docker-entrypoint-initdb.d
│   └── init.sql         # миграции БД
├── postman              # коллекция Postman
├── scripts              # утилиты для генерации данных
└── README.md
```
### Тесты
coming soon

### Автор
Максим Глотов