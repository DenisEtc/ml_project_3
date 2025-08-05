import pika
import json

RABBITMQ_HOST = "rabbitmq"

def send_task_to_queue(task: dict):
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue="ml_tasks", durable=True)
    message = json.dumps(task)
    channel.basic_publish(exchange="", routing_key="ml_tasks", body=message)
    connection.close()
