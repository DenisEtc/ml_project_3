from app.db import Base, engine, SessionLocal
from app.models.user import User, UserRole
from app.models.ml_model import MLModel
import hashlib

def init_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin = User(username="admin", email="admin@example.com", password_hash=hashlib.sha256("admin123".encode()).hexdigest(), role=UserRole.ADMIN, balance=1000.0)
        user = User(username="john_doe", email="john@example.com", password_hash=hashlib.sha256("password123".encode()).hexdigest(), role=UserRole.USER, balance=100.0)
        model = MLModel(name="Heart Failure Predictor", description="Predict heart failure risk", cost_per_prediction=10.0)
        db.add_all([admin, user, model])
        db.commit()
        print("Database initialized with demo data")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
