from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Optional
import re

# Роли пользователя
class UserRole(Enum):
    USER = "user"
    ADMIN = "admin"

# Статусы задач
class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# Класс пользователя
@dataclass
class User:
    """
    Класс для представления пользователя системы.
    """
    id: int
    username: str
    email: str
    password: str
    role: UserRole = UserRole.USER
    balance: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        self._validate_email()
        self._validate_username()
        self._validate_password()

    def _validate_email(self):
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', self.email):
            raise ValueError("Invalid email format")

    def _validate_username(self):
        if len(self.username) < 3:
            raise ValueError("Username must be at least 3 characters long")

    def _validate_password(self):
        if len(self.password) < 8:
            raise ValueError("Password must be at least 8 characters long")

    def deposit(self, amount: float):
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        self.balance += amount
        self._update_timestamp()

    def withdraw(self, amount: float):
        if amount > self.balance:
            raise ValueError("Insufficient balance")
        self.balance -= amount
        self._update_timestamp()

    def _update_timestamp(self):
        self.updated_at = datetime.utcnow()

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
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def set_status(self, status: TaskStatus):
        self.status = status
        self._update_timestamp()

    def set_result(self, result: Dict):
        self.result_data = result
        self.status = TaskStatus.COMPLETED
        self._update_timestamp()

    def _update_timestamp(self):
        self.updated_at = datetime.utcnow()
