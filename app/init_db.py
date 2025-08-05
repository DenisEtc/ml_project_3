from shared.db import engine, Base, SessionLocal
from shared.models.user import User
from shared.models.transaction import Transaction
from shared.models.ml_model import MLModel
from shared.models.prediction import Prediction
from app.services.auth_service import get_password_hash

# Создаём таблицы
Base.metadata.create_all(bind=engine)

# Инициализируем демо-данные
db = SessionLocal()

# Проверим, есть ли админ
admin = db.query(User).filter(User.username == "admin").first()
if not admin:
    admin = User(username="admin", email="admin@example.com", password_hash=get_password_hash("admin"), balance=1000)
    db.add(admin)

# Проверим, есть ли тестовая ML-модель
model = db.query(MLModel).filter(MLModel.name == "Heart Failure Model").first()
if not model:
    model = MLModel(name="Heart Failure Model", description="Predict heart failure risk", price=10)
    db.add(model)

db.commit()
db.close()

print("✅ Database initialized with demo data")
