FROM python:3.11-slim

WORKDIR /worker

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Код worker и shared монтируем через volumes
CMD ["python", "worker/worker.py"]
