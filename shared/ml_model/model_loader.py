import pickle
import os

MODEL_PATH = os.getenv("MODEL_PATH", "shared/ml_model/heart_failure.pkl")

def load_model():
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    return model
