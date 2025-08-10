import json
import os
import time
from typing import Tuple, Dict

import pika
from pika.exceptions import AMQPConnectionError
from sqlalchemy.orm import Session

from shared.db import SessionLocal
from shared.models.prediction import Prediction
from shared.models.user import User
from shared.models.transaction import Transaction

RABBIT_HOST = os.getenv("RABBIT_HOST", "rabbitmq")
RABBIT_USER = os.getenv("RABBIT_USER", "guest")
RABBIT_PASSWORD = os.getenv("RABBIT_PASSWORD", "guest")
QUEUE_NAME = os.getenv("QUEUE_NAME", "ml_tasks")

FEATURE_ORDER = [s.strip() for s in os.getenv("FEATURE_ORDER", "feature1,feature2,feature3").split(",") if s.strip()]
_WEIGHTS = [s.strip() for s in os.getenv("WEIGHTS", "0.7,0.2,0.1").split(",") if s.strip()]
try:
    WEIGHTS = [float(s) for s in _WEIGHTS]
except ValueError:
    WEIGHTS = [0.7, 0.2, 0.1]
BIAS = float(os.getenv("BIAS", "0.0"))

if len(WEIGHTS) < len(FEATURE_ORDER):
    WEIGHTS = WEIGHTS + [0.0] * (len(FEATURE_ORDER) - len(WEIGHTS))
elif len(WEIGHTS) > len(FEATURE_ORDER):
    WEIGHTS = WEIGHTS[: len(FEATURE_ORDER)]


def split_valid_invalid(records: Dict) -> Tuple[Dict, Dict]:
    valid, invalid = {}, {}
    for k, v in records.items():
        if isinstance(v, (int, float)):
            valid[k] = float(v)
        else:
            invalid[k] = v
    return valid, invalid


def linear_predict(valid_input: Dict[str, float]) -> float:
    total = BIAS
    for name, w in zip(FEATURE_ORDER, WEIGHTS):
        total += float(valid_input.get(name, 0.0)) * w
    return total


def handle_task(db: Session, task: dict):
    user_id = int(task["user_id"])
    model_id = int(task["model_id"])
    input_data = task["input_data"]
    price = float(task["price"])

    print(f"[worker] task: user_id={user_id} model_id={model_id} price={price} input={input_data}")

    user: User | None = (
        db.query(User)
        .filter(User.id == user_id)
        .with_for_update(read=False)
        .first()
    )
    if not user:
        print(f"[worker] skip: user {user_id} not found")
        return

    if user.balance < price:
        print(f"[worker] skip: insufficient balance (balance={user.balance}, price={price})")
        return

    valid, invalid = split_valid_invalid(input_data)
    if not valid:
        print(f"[worker] skip: no valid features after validation. invalid={invalid}")
        return

    y = linear_predict(valid)
    pred_value = f"{y:.4f}"

    user.balance -= price
    db.add(Transaction(user_id=user_id, amount=price, type="withdraw"))
    db.add(Prediction(user_id=user_id, model_id=model_id, prediction=pred_value, cost=price))
    db.commit()

    print(f"[worker] done: prediction={pred_value}, withdrawn={price}, new_balance={user.balance}")


def _open_channel_with_retry():
    creds = pika.PlainCredentials(RABBIT_USER, RABBIT_PASSWORD)
    params = pika.ConnectionParameters(
        host=RABBIT_HOST,
        credentials=creds,
        heartbeat=30,
        blocked_connection_timeout=30,
    )
    attempt = 0
    while True:
        attempt += 1
        try:
            print(f"[*] connecting to RabbitMQ {RABBIT_HOST} (attempt {attempt})")
            conn = pika.BlockingConnection(params)
            ch = conn.channel()
            ch.queue_declare(queue=QUEUE_NAME, durable=True)
            print(f"[*] connected, listening on queue '{QUEUE_NAME}'")
            return ch, conn
        except AMQPConnectionError as e:
            wait = min(10, attempt * 2)
            print(f"[!] AMQPConnectionError: {e}. retry in {wait}s")
            time.sleep(wait)


def main():
    print(f"[*] Worker boot. host={RABBIT_HOST} queue={QUEUE_NAME} user={RABBIT_USER}")
    channel, connection = _open_channel_with_retry()

    def callback(ch, method, properties, body):
        try:
            task = json.loads(body.decode("utf-8"))
        except Exception as e:
            print(f"[worker] bad message: {e}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        db = SessionLocal()
        try:
            handle_task(db, task)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"[worker] error: {e}. requeue")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        finally:
            db.close()

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=False)
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        try:
            channel.stop_consuming()
        except Exception:
            pass
        try:
            connection.close()
        except Exception:
            pass


if __name__ == "__main__":
    time.sleep(int(os.getenv("WORKER_STARTUP_DELAY", "2")))
    main()
