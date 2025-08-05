FROM python:3.11-slim

WORKDIR /worker

COPY ../../requirements_worker.txt .
RUN pip install --no-cache-dir -r requirements_worker.txt

COPY ./app ./app

CMD ["python", "app/workers/worker.py"]
