# Базовый образ Python
FROM python:3.11-slim

# Рабочая директория
WORKDIR /app

# Копируем файл зависимостей и устанавливаем их
COPY ./app/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код приложения
COPY ./app ./app
COPY ./shared ./shared

# Добавляем /app в PYTHONPATH
ENV PYTHONPATH=/app

# Команда запуска FastAPI через Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
