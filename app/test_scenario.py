from app.db import SessionLocal
from app.services.user_service import create_user
from app.services.transaction_service import deposit, withdraw, get_transaction_history

def run_test():
    db = SessionLocal()
    try:
        print("=== TEST SCENARIO START ===")

        # Создаём нового пользователя
        user = create_user(db, "test_user", "test@example.com", "secure123")
        print(f"User created: {user.username}, balance={user.balance}")

        # Пополняем баланс
        deposit(db, user.id, 200)
        print(f"Balance after deposit: {user.balance}")

        # Списываем средства
        withdraw(db, user.id, 50)
        print(f"Balance after withdraw: {user.balance}")

        # История транзакций
        transactions = get_transaction_history(db, user.id)
        for t in transactions:
            print(f"Transaction: {t.type.value} {t.amount} at {t.created_at}")

        print("=== TEST SCENARIO END ===")
    finally:
        db.close()

if __name__ == "__main__":
    run_test()
