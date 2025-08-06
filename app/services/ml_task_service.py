import json
import pika
import requests


def send_task_to_queue(user_id: int, model_id: int, input_data: dict):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='ml_rabbit'))
    channel = connection.channel()
    channel.queue_declare(queue='ml_tasks')

    task = {
        "user_id": user_id,
        "model_id": model_id,
        "input_data": input_data
    }

    channel.basic_publish(
        exchange='',
        routing_key='ml_tasks',
        body=json.dumps(task)
    )

    connection.close()


def run_sync_prediction(model_id: int, input_data: dict) -> float:
    """
    Выполняет синхронный HTTP-запрос к ML модели внутри контейнера.
    """
    response = requests.post(
        "http://ml_worker1:8001/predict",
        json={"model_id": model_id, "input_data": input_data}
    )

    if response.status_code == 200:
        return response.json().get("prediction")
    else:
        return -1  # можно заменить на None или выбросить исключение
