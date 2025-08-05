import json
import pika
import time
import pickle
import os
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models.prediction import Prediction

MODEL_PATH = "app/ml_model/heart_failure.pkl"
RABBITMQ_HOST = "rabbitmq"

# Загружаем модель при старте
with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

def callback(ch, method, properties, body):
    print(f"[x] Received {body}")
    data = json.loads(body)

    # Проверка данных
    if "input_data" not in data or not isinstance(data["input_data"], dict):
        print("[!] Invalid data format")
        return

    # Предсказание
    features = [v for v in data["input_data"].values()]
    prediction_result = model.predict([features])[0]

    # Сохраняем результат
    db: Session = SessionLocal()
    new_prediction = Prediction(
        user_id=data["user_id"],
        model_id=data["model_id"],
        prediction=str(prediction_result)
    )
    db.add(new_prediction)
    db.commit()
    db.close()

    print(f"[x] Prediction saved for user {data['user_id']}")

def main():
    time.sleep(5)  # Ждём RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue="ml_tasks", durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue="ml_tasks", on_message_callback=callback, auto_ack=True)
    print("[*] Worker started. Waiting for messages.")
    channel.start_consuming()

if __name__ == "__main__":
    main()
