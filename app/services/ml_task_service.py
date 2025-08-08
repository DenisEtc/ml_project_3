import json
import pika

RABBIT_HOST = "rabbitmq"
QUEUE_NAME = "ml_tasks"

def send_task_to_queue(user_id: int, model_id: int, input_data: dict) -> None:
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    task = {
        "user_id": user_id,
        "model_id": model_id,
        "input_data": input_data
    }
    body = json.dumps(task).encode("utf-8")

    # Деливери-флаг как устойчивое сообщение
    channel.basic_publish(
        exchange="",
        routing_key=QUEUE_NAME,
        body=body,
        properties=pika.BasicProperties(delivery_mode=2)
    )
    connection.close()
