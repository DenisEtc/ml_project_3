from sqlalchemy.orm import Session
from app.models.transaction import Transaction, TransactionType
from app.models.user import User

def deposit(db: Session, user_id: int, amount: float):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("User not found")
    user.balance += amount
    transaction = Transaction(user_id=user.id, amount=amount, type=TransactionType.DEPOSIT)
    db.add(transaction)
    db.commit()
    return transaction

def withdraw(db: Session, user_id: int, amount: float):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("User not found")
    if user.balance < amount:
        raise ValueError("Insufficient balance")
    user.balance -= amount
    transaction = Transaction(user_id=user.id, amount=amount, type=TransactionType.WITHDRAW)
    db.add(transaction)
    db.commit()
    return transaction

def get_transaction_history(db: Session, user_id: int):
    return db.query(Transaction).filter(Transaction.user_id == user_id).all()
