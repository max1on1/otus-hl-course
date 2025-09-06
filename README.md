# Что есть в проекте
- Backend на **FastAPI**
- База данных **PostgreSQL** с репликацией
- Подключение к БД через `asyncpg`
- Кеширование ленты друзей в **Redis**
- Обмен сообщениями через **RabbitMQ**
- Сервис диалогов вынесен в отдельный сервис (REST)
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

API-шлюз (nginx)
http://localhost:8000

Монолит (FastAPI)
http://app:8000 (внутри сети docker)

Dialog Service (FastAPI)
http://dialog-service:8001 (внутри сети docker)

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
│   ├── dialog_client.py # REST‑клиент диалог-сервиса
│   ├── dialogs.py       # (legacy) старая имплементация, не используется
│   ├── mq.py            # работа с RabbitMQ
│   └── Dockerfile       # образ приложения
├── dialog-service       # выделенный сервис диалогов
│   ├── main.py          # HTTP API сервиса
│   ├── dialog_db.py     # доступ к шардированной БД
│   ├── models.py        # модели
│   └── Dockerfile       # образ сервиса
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

## Миграция диалогов в отдельный сервис

Описание протокола взаимодействия и обратная совместимость:

- Старые клиенты: продолжают использовать эндпоинты монолита
  - POST `/dialog/{userId}/send`
  - GET  `/dialog/{userId}/list`
  Монолит проксирует запросы в Dialog Service и возвращает ответы в прежнем формате.

- Новые клиенты: могут ходить напрямую через новый API-шлюз к Dialog Service
  - POST `/api/v1/dialog/{userId}/send`
  - GET  `/api/v1/dialog/{userId}/list`

- Аутентификация: передается через `Authorization: Bearer <JWT>`; обе службы используют единый `SECRET_KEY`.

- Сквозное логирование: используется заголовок `x-request-id`.
  - Nginx добавляет/пробрасывает `x-request-id` к монолиту и сервису диалогов.
  - Монолит и диалог‑сервис возвращают `x-request-id` в ответе и прокидывают его дальше при внутренних REST‑вызовах.

Переменные окружения:
- Монолит: `DIALOG_SERVICE_URL` указывает на `http://dialog-service:8001`.
- Диалог‑сервис: `DIALOG_DB_DSNS` — список DSN через запятую для шардинга сообщений.

Запуск:
- `docker-compose up --build`
- API: старое `/dialog/...` через `http://localhost:8000`, новое `/api/v1/dialog/...` через тот же адрес.
