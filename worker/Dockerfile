FROM python:3.11-slim

# Рабочая директория для воркера
WORKDIR /worker

# Копируем зависимости для воркера
COPY ./worker/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копируем файл с логикой воркера
COPY ./worker/worker.py ./worker.py

# Запуск воркера
CMD ["python", "worker.py"]
