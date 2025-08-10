import json
import os
import time
from typing import Tuple, List, Dict

import pika
from sqlalchemy.orm import Session

from shared.db import SessionLocal
from shared.models.prediction import Prediction
from shared.models.user import User
from shared.models.transaction import Transaction

RABBIT_HOST = os.getenv("RABBIT_HOST", "rabbitmq")
QUEUE_NAME = os.getenv("QUEUE_NAME", "ml_tasks")


def split_valid_invalid(records: Dict) -> Tuple[Dict, Dict]:
    """Простейшая валидация: числовые значения -> валидно, остальное -> невалидно"""
    valid, invalid = {}, {}
    for k, v in records.items():
        if isinstance(v, (int, float)):
            valid[k] = v
        else:
            invalid[k] = v
    return valid, invalid


def do_predict(valid_input: Dict) -> str:
    # Для демо — константа; тут можно загрузить pickle и дернуть model.predict
    return "0.42"


def handle_task(db: Session, task: dict):
    user_id = int(task["user_id"])
    model_id = int(task["model_id"])
    input_data = task["input_data"]
    price = float(task["price"])

    user = db.query(User).filter(User.id == user_id).with_for_update(read=False).first()
    if not user:
        return

    if user.balance < price:
        # недостаточно средств — просто игнорируем (в реале можно отправить событие пользователю)
        return

    valid, invalid = split_valid_invalid(input_data)
    if not valid:
        # ничего валидного — не списываем
        return

    pred_value = do_predict(valid)
    # списываем средства
    user.balance -= price
    db.add(Transaction(user_id=user_id, amount=price, type="withdraw"))
    db.add(Prediction(user_id=user_id, model_id=model_id, prediction=pred_value, cost=price))
    db.commit()


def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    def callback(ch, method, properties, body):
        try:
            task = json.loads(body.decode("utf-8"))
        except Exception:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        db = SessionLocal()
        try:
            handle_task(db, task)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception:
            # при ошибке не теряем сообщение
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        finally:
            db.close()

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=False)
    print("[*] Worker started. Waiting for messages...")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        try:
            channel.stop_consuming()
        except Exception:
            pass
        connection.close()


if __name__ == "__main__":
    time.sleep(int(os.getenv("WORKER_STARTUP_DELAY", "2")))
    main()
