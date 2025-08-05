from sqlalchemy.orm import Session
from shared.models.transaction import Transaction
from shared.models.user import User

def create_transaction(db: Session, user_id: int, amount: float, type: str):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    if type == "withdraw" and user.balance < amount:
        return None

    if type == "deposit":
        user.balance += amount
    elif type == "withdraw":
        user.balance -= amount

    transaction = Transaction(user_id=user_id, amount=amount, type=type)
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction

def get_transactions(db: Session, user_id: int):
    return db.query(Transaction).filter(Transaction.user_id == user_id).all()
