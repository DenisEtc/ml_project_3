import json
import pika
import time
from app.ml_model.model_loader import model
from app.db import SessionLocal
from app.models.ml_task import MLTask
from app.models.prediction_history import PredictionHistory

RABBITMQ_HOST = "rabbitmq"

def callback(ch, method, properties, body):
    print(f" [x] Received {body}")
    data = json.loads(body)

    # Валидация данных
    if "input_data" not in data or not isinstance(data["input_data"], dict):
        print("Invalid data format")
        return

    # Предсказание
    features = [v for v in data["input_data"].values()]
    prediction = model.predict([features])[0]

    # Сохранение в БД
    db = SessionLocal()
    history = PredictionHistory(user_id=data["user_id"], model_id=data["model_id"], prediction=str(prediction))
    db.add(history)
    db.commit()
    db.close()

    print(f" [x] Prediction saved for user {data['user_id']}")

def main():
    time.sleep(5)  # Ждём RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue="ml_tasks", durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue="ml_tasks", on_message_callback=callback, auto_ack=True)
    print(" [*] Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()

if __name__ == "__main__":
    main()
