from models import User, MLModel, MLTask, TaskStatus, DepositTransaction, WithdrawTransaction, TransactionHistory, PredictionHistory

def main():
    # Создаём пользователя
    user = User.create(id=1, username="john_doe", email="john@example.com", password="securePass123")
    print(f"Пользователь: {user.username}, баланс: {user.balance.amount}")

    # Транзакции
    tx_history = TransactionHistory()
    tx_history.add_transaction(DepositTransaction(id=1, user=user, amount=100.0))
    tx_history.add_transaction(WithdrawTransaction(id=2, user=user, amount=30.0))
    print(f"Баланс после транзакций: {user.balance.amount}")

    # Модель и задача
    model = MLModel(id=1, name="Heart Failure Predictor", description="Predict heart failure risk", cost_per_prediction=10.0)
    task = MLTask(id=1, user=user, model=model, input_data={"age": 60, "bp": 120})

    # История предсказаний
    prediction_history = PredictionHistory()
    prediction_history.add_prediction(task)
    task.set_status(TaskStatus.COMPLETED)
    task.set_result({"prediction": 1, "probability": 0.82})

    print(f"Результат задачи: {task.result_data}")
    print(f"История предсказаний: {len(prediction_history.predictions)}")

if __name__ == "__main__":
    main()
