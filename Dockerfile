FROM python:3.11-slim

WORKDIR /app

# Копируем только requirements, чтобы использовать кэш при пересборке
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Остальной код будет подключен через volumes, так что COPY не нужен
ENV PYTHONPATH=/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
