import json
import pika
import time
import pickle
import os
from sqlalchemy.orm import Session
from shared.db import SessionLocal
from shared.models.prediction import Prediction

# Пути и конфигурация
MODEL_PATH = "shared/ml_model/heart_failure.pkl"
RABBITMQ_HOST = "rabbitmq"

# Загружаем ML модель при старте
print("[*] Loading ML model...")
with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)
print("[*] Model loaded successfully.")

def callback(ch, method, properties, body):
    # Обработка входящих задач из очереди RabbitMQ
    print(f"[x] Received task: {body}")
    data = json.loads(body)

    # Проверка корректности данных
    if "input_data" not in data or not isinstance(data["input_data"], dict):
        print("[!] Invalid data format")
        return

    # Подготовка данных для предсказания
    try:
        features = [v for v in data["input_data"].values()]
        prediction_result = model.predict([features])[0]
    except Exception as e:
        print(f"[!] Error during prediction: {e}")
        return

    # Сохраняем результат в БД
    db: Session = SessionLocal()
    try:
        new_prediction = Prediction(
            user_id=data["user_id"],
            model_id=data["model_id"],
            prediction=str(prediction_result)
        )
        db.add(new_prediction)
        db.commit()
        print(f"[+] Prediction saved for user {data['user_id']}")
    except Exception as e:
        db.rollback()
        print(f"[!] Error saving prediction: {e}")
    finally:
        db.close()

def main():
    # Запускаем обработчик очереди
    print("[*] Waiting for RabbitMQ to start...")
    time.sleep(5)  # Ждём RabbitMQ

    print("[*] Connecting to RabbitMQ...")
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue="ml_tasks", durable=True)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue="ml_tasks", on_message_callback=callback, auto_ack=True)

    print("[*] Worker started. Waiting for messages...")
    channel.start_consuming()

if __name__ == "__main__":
    main()
