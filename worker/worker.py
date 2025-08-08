import json
import os
import pickle
import time

import pika
from sqlalchemy.orm import Session

from shared.db import SessionLocal
from shared.models.prediction import Prediction

RABBIT_HOST = os.getenv("RABBIT_HOST", "rabbitmq")
QUEUE_NAME = os.getenv("QUEUE_NAME", "ml_tasks")
MODEL_PATH = os.getenv("MODEL_PATH", "shared/ml_model/heart_failure.pkl")

def load_model():
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)

def handle_task(ch, method, properties, body, model):
    try:
        data = json.loads(body.decode("utf-8"))
        user_id = data["user_id"]
        model_id = data["model_id"]
        input_data = data["input_data"]

        try:
            pred_value = float(model.predict([input_data])[0])
        except Exception:
            # fallback
            pred_value = 0.0

        # Сохраняем предсказание
        db: Session = SessionLocal()
        try:
            pred_row = Prediction(
                user_id=user_id,
                model_id=model_id,
                prediction=str(pred_value),
            )
            db.add(pred_row)
            db.commit()
        finally:
            db.close()

    except Exception as e:
        print("[!] Error while processing task:", e)

def main():
    print("[*] Loading ML model...")
    model = load_model()

    print("[*] Connecting to RabbitMQ...")
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBIT_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_qos(prefetch_count=1)

    def callback(ch, method, properties, body):
        handle_task(ch, method, properties, body, model)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=False)
    print("[*] Worker started. Waiting for messages...")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Stopping...")
        try:
            channel.stop_consuming()
        except Exception:
            pass
        connection.close()

if __name__ == "__main__":
    time.sleep(int(os.getenv("WORKER_STARTUP_DELAY", "2")))
    main()
