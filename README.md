# Что есть в проекте
	•	Backend на FastAPI
	•	База данных PostgreSQL
	•	Подключение через asyncpg
	•	Контейнеризация через Docker и docker-compose
	•	Чистые миграции в SQL
	•	Готовая коллекция запросов для Postman


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
├── app
│   ├── db.py
│   ├── Dockerfile
│   ├── handlers.py
│   ├── main.py
│   ├── models.py
│   └── requirements.txt
├── docker-compose.yml
├── migrations
│   └── create_tables.py
├── postman <- Postman collection
│   ├── otus-hl-course.postman_collection.json 
│   └── otus-hl-env.postman_environment.json
├── README.md
└── tests
    └── test_endpoints.py <- автотесты pytest 
```
### Тесты
Навсякий случай можно протестировать pytest

### Автор
Максим Глотов