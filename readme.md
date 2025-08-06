## Основной функционал

* Регистрация и аутентификация пользователей (JWT)
* Пополнение баланса
* Создание ML-задачи для предсказания
* Обработка задач несколькими воркерами через RabbitMQ
* Веб-интерфейс для работы с системой
* API-документация (Swagger)

---

## Стек технологий

* **Backend:** FastAPI
* **Frontend:** HTML, CSS (шаблоны Jinja2)
* **База данных:** PostgreSQL + SQLAlchemy
* **Очередь сообщений:** RabbitMQ
* **ML:** Python, pickle-модель
* **Контейнеризация:** Docker, Docker Compose
* **Обратный прокси:** Nginx

---

## Структура проекта

```
project/
├── app/                # Веб-приложение (FastAPI)
│   ├── main.py         # Точка входа
│   ├── routes/         # Маршруты (API + Web)
│   ├── schemas/        # Pydantic-схемы
│   ├── services/       # Логика работы
│   ├── templates/      # HTML-шаблоны
│   ├── static/         # CSS
│   └── tests/          # Тестовые сценарии
├── shared/             # Общий код для app и worker
│   ├── db.py           # Подключение к БД
│   ├── models/         # SQLAlchemy модели
│   └── ml_model/       # ML модель и загрузчик
├── worker/             # Код ML-воркера
│   ├── worker.py       # Основная логика
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml  # Настройка сервисов
├── Dockerfile          # Для FastAPI-приложения
├── nginx.conf          # Конфиг Nginx
└── requirements.txt    # Зависимости для app
```

---

## Установка и запуск

### 1. Клонирование репозитория

```bash
git clone <repo_url>
cd project
```

### 2. Запуск через Docker Compose

```bash
docker-compose down --volumes --remove-orphans
docker-compose up --build -d
```

После успешного запуска доступно:

* Веб-интерфейс: [http://localhost](http://localhost)
* Swagger API: [http://localhost/docs](http://localhost/docs)
* RabbitMQ панель: [http://localhost:15672](http://localhost:15672) (логин: guest, пароль: guest)

---

## Тестирование функционала

### Регистрация

Через веб-интерфейс `/register` или API:

```http
POST /auth/register
```

### Логин

Через `/login` или API:

```http
POST /auth/login
```

### Пополнение баланса

```http
POST /deposit
```

### Создание задачи для предсказания

```http
POST /predict
```

Пример данных:

```json
{
  "user_id": 1,
  "model_id": 1,
  "input_data": {"age": 65, "cholesterol": 250, "bp": 130}
}
```

### Проверка очереди

Задачи попадают в RabbitMQ → Обрабатываются воркерами → Результаты сохраняются в БД.

---

## Проверка работы воркеров

Просмотр логов:

```bash
docker logs worker1
```

---

## API-документация

Swagger доступен по адресу:

```
http://localhost/docs
```

---

## Требования

* Docker, Docker Compose
* Порт `80` свободен (для Nginx)
* Порт `5432` (PostgreSQL)
* Порт `15672` (RabbitMQ Management UI)

---
