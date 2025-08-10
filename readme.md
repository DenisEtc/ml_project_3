# ML Service
Личный кабинет пользователя ML сервиса

## Описание

Веб-приложение, реализующее личный кабинет пользователя ML-сервиса.  
Функционал включает:
- Регистрация и авторизация пользователей (JWT).
- Просмотр и пополнение баланса в условных кредитах.
- Выполнение запросов к ML-сервису (с оплатой в кредитах).
- История транзакций и предсказаний.
- REST API и Web-интерфейс.
- Асинхронная обработка задач через RabbitMQ и воркеров.

В проекте предусмотрена валидация входных данных и проверка положительного баланса перед выполнением запросов.

---

## Структура проекта

```
app/                 # Backend API и web-маршруты
shared/              # Общие модели и настройки
worker/              # Код воркеров
tests/               # Автотесты
docker-compose.yml   # Конфигурация сервисов
Dockerfile           # Сборка образа приложения
```

## Стек технологий

- **Backend**: Python 3.11, FastAPI, SQLAlchemy
- **База данных**: PostgreSQL
- **Очереди**: RabbitMQ
- **Фронтенд**: Jinja2 templates (через FastAPI)
- **Аутентификация**: OAuth2, JWT
- **Тестирование**: pytest
- **Инфраструктура**: Docker, docker-compose

---

## Запуск проекта

### 1. Клонирование репозитория
```bash
git clone <url_репозитория>
cd <папка_проекта>
````

### 2. Настройка окружения

Создайте файл `.env` в корне проекта. Минимальный набор переменных:

```env
POSTGRES_USER=app
POSTGRES_PASSWORD=app
POSTGRES_DB=app
DATABASE_URL=postgresql+psycopg2://app:app@ml_postgres:5432/app
SECRET_KEY=dev_secret
ACCESS_TOKEN_EXPIRE_MINUTES=60
RABBIT_HOST=rabbitmq
QUEUE_NAME=ml_tasks
TEST_MODE=1
```

`TEST_MODE=1` включает синхронный режим предсказаний (для локальной проверки без воркеров).

### 3. Сборка и запуск

```bash
docker compose up -d --build
```

При первом запуске создайте демо-данные:

```bash
docker exec -it ml_app bash -lc "python -m app.init_db"
```

---

## Проверка функциональности

### Вариант A — через Web-интерфейс

1. Открой браузер: [http://localhost:8000/web](http://localhost:8000/web)
2. Зарегистрируйте нового пользователя.
3. Войдите под созданной учётной записью.
4. Пополните баланс (например, на 10 кредитов).
5. Выберите модель из списка и введите входные признаки.
6. Нажмите **Сделать предсказание**:

   * Баланс уменьшится на цену модели.
   * В истории транзакций появится списание (`withdraw`).
   * В истории предсказаний появится новый результат.

### Вариант B — через REST API

Пример с `curl`:

```bash
API=http://localhost:8000

# Регистрация
curl -X POST $API/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","password":"test123"}'

# Логин и получение токена
TOKEN=$(curl -s -X POST $API/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'username=alice&password=test123' | jq -r .access_token)

# Получение user_id
USER_ID=$(curl -s -H "Authorization: Bearer $TOKEN" $API/users/me | jq -r .id)

# Пополнение баланса
curl -X POST $API/transactions/deposit \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id":'$USER_ID',"amount":10,"type":"deposit"}'

# Предсказание
MODEL_ID=<id_существующей_модели>
curl -X POST $API/predict \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id":'$USER_ID',"model_id":'$MODEL_ID',"input_data":{"feature1":1.0,"feature2":2.0,"feature3":3.0}}'
```

---

## Боевой режим (с воркерами)

Для асинхронной работы:

1. Установите `TEST_MODE=0` в `.env` или удалите переменную.
2. Перезапустите проект:

   ```bash
   docker compose down -v
   docker compose up -d --build
   ```
3. Предсказания будут отправляться в RabbitMQ и обрабатываться контейнером `ml_worker`.
4. Очередь задач доступна в UI RabbitMQ: [http://localhost:15672](http://localhost:15672) (логин/пароль `guest`/`guest`).

---

## Тестирование

Интеграционные тесты выполняются в контейнере `ml_tests`:

```bash
docker logs ml_tests
```

или вручную:

```bash
docker run --rm --network=project_default \
  -e API_BASE_URL=http://ml_app:8000 \
  project-tests:latest pytest -q
```