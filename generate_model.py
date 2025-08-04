import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import make_classification

# Генерируем набор данных
X, y = make_classification(n_samples=500, n_features=5, random_state=42)

# Обучаем модель
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

# Сохраняем модель в файл
MODEL_PATH = "app/ml_model/heart_failure.pkl"
with open(MODEL_PATH, "wb") as f:
    pickle.dump(model, f)

print(f"Модель сохранена в {MODEL_PATH}")
