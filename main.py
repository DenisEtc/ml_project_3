from models import User, MLModel, MLTask, TaskStatus, UserRole

def main():
    # Создаем пользователя
    user = User(id=1, username="john_doe", email="john@example.com", password="securePass123")
    print(f"Создан пользователь: {user.username}, баланс: {user.balance}")

    # Пополняем баланс
    user.deposit(100.0)
    print(f"Баланс после пополнения: {user.balance}")

    # Создаем ML модель
    model = MLModel(id=1, name="Heart Failure Predictor", description="Predict heart failure risk", cost_per_prediction=10.0)

    # Создаем ML задачу
    task = MLTask(id=1, user=user, model=model, input_data={"age": 60, "bp": 120})
    print(f"Создана задача со статусом: {task.status.value}")

    # Изменяем статус и добавляем результат
    task.set_status(TaskStatus.PROCESSING)
    task.set_result({"prediction": 1, "probability": 0.82})
    print(f"Задача завершена. Результат: {task.result_data}")

if __name__ == "__main__":
    main()
