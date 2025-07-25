from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, List
import re
import hashlib
from abc import ABC, abstractmethod

# Роли и статусы
class UserRole(Enum):
    USER = "user"
    ADMIN = "admin"


class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# Баланс
@dataclass
class Balance:
    """
    Класс для управления балансом.
    """
    amount: float = 0.0

    def deposit(self, value: float):
        if value <= 0:
            raise ValueError("Deposit amount must be positive")
        self.amount += value

    def withdraw(self, value: float):
        if value > self.amount:
            raise ValueError("Insufficient balance")
        self.amount -= value


# Пользователь
@dataclass
class User:
    """
    Класс для представления пользователя.
    """
    id: int
    username: str
    email: str
    _password_hash: str = field(repr=False)
    role: UserRole = UserRole.USER
    balance: Balance = field(default_factory=Balance)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        self._validate_email()
        self._validate_username()

    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    @classmethod
    def create(cls, id: int, username: str, email: str, password: str):
        return cls(id=id, username=username, email=email, _password_hash=cls.hash_password(password))

    def check_password(self, password: str) -> bool:
        return self._password_hash == self.hash_password(password)

    def _validate_email(self):
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', self.email):
            raise ValueError("Invalid email format")

    def _validate_username(self):
        if len(self.username) < 3:
            raise ValueError("Username must be at least 3 characters long")

# ML Модель
@dataclass
class MLModel:
    id: int
    name: str
    description: str
    cost_per_prediction: float


# ML Задача
@dataclass
class MLTask:
    id: int
    user: User
    model: MLModel
    input_data: Dict
    result_data: Optional[Dict] = None
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)

    def set_status(self, status: TaskStatus):
        self.status = status

    def set_result(self, result: Dict):
        self.result_data = result
        self.status = TaskStatus.COMPLETED

# Абстрактная транзакция (полиморфизм)
@dataclass
class Transaction(ABC):
    id: int
    user: User
    amount: float
    created_at: datetime = field(default_factory=datetime.utcnow)

    @abstractmethod
    def apply(self):
        pass


@dataclass
class DepositTransaction(Transaction):
    def apply(self):
        self.user.balance.deposit(self.amount)


@dataclass
class WithdrawTransaction(Transaction):
    def apply(self):
        self.user.balance.withdraw(self.amount)

# История транзакций и предсказаний
@dataclass
class TransactionHistory:
    transactions: List[Transaction] = field(default_factory=list)

    def add_transaction(self, transaction: Transaction):
        transaction.apply()
        self.transactions.append(transaction)


@dataclass
class PredictionHistory:
    predictions: List[MLTask] = field(default_factory=list)

    def add_prediction(self, task: MLTask):
        self.predictions.append(task)
