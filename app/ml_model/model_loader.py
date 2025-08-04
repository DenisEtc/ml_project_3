import pickle
import os

MODEL_PATH = "app/ml_model/heart_failure.pkl"

def load_model():
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    return model

# Грузим модель один раз при старте
model = load_model()
