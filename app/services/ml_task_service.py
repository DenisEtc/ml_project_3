import json
import os
from typing import Any, Dict

import pika

RABBIT_HOST = os.getenv("RABBIT_HOST", "rabbitmq")
RABBIT_USER = os.getenv("RABBIT_USER", "guest")
RABBIT_PASSWORD = os.getenv("RABBIT_PASSWORD", "guest")
QUEUE_NAME = os.getenv("QUEUE_NAME", "ml_tasks")


def _open_channel():
    creds = pika.PlainCredentials(RABBIT_USER, RABBIT_PASSWORD)
    params = pika.ConnectionParameters(
        host=RABBIT_HOST,
        credentials=creds,
        heartbeat=30,
        blocked_connection_timeout=30,
        connection_attempts=5,
        retry_delay=2.0,
    )
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    return channel, connection


def send_task_to_queue(*, user_id: int, model_id: int, input_data: Dict[str, Any], price: float) -> None:
    payload = {
        "user_id": int(user_id),
        "model_id": int(model_id),
        "input_data": input_data,
        "price": float(price),
    }
    body = json.dumps(payload).encode("utf-8")

    channel, connection = _open_channel()
    try:
        channel.basic_publish(
            exchange="",
            routing_key=QUEUE_NAME,
            body=body,
            properties=pika.BasicProperties(
                delivery_mode=2,  # persistent
                content_type="application/json",
            ),
        )
        print(f"[publisher] sent -> {QUEUE_NAME}: {payload}")
    finally:
        try:
            connection.close()
        except Exception:
            pass
