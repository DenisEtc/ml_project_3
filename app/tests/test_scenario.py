import requests
import time

BASE_URL = "http://localhost:8000"
USERNAME = "test_user"
PASSWORD = "test_password"
EMAIL = "test_user@example.com"

def register_user():
    print("[+] Registering user...")
    response = requests.post(f"{BASE_URL}/auth/register", params={
        "username": USERNAME,
        "email": EMAIL,
        "password": PASSWORD
    })
    print("Register response:", response.status_code, response.json())

def login_user():
    print("[+] Logging in...")
    response = requests.post(f"{BASE_URL}/auth/login", data={
        "username": USERNAME,
        "password": PASSWORD
    })
    print("Login response:", response.status_code, response.json())
    return response.json()["access_token"]

def deposit(token, user_id, amount=100):
    print("[+] Depositing balance...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/deposit", params={
        "user_id": user_id,
        "amount": amount
    }, headers=headers)
    print("Deposit response:", response.status_code, response.json())

def predict(token, user_id):
    print("[+] Sending prediction task...")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "user_id": user_id,
        "model_id": 1,
        "input_data": {"feature1": 50, "feature2": 230, "feature3": 1, "feature4": 0, "feature5": 120}
    }
    response = requests.post(f"{BASE_URL}/predict", json=payload, headers=headers)
    print("Predict response:", response.status_code, response.json())

def get_predictions(token, user_id):
    print("[+] Fetching prediction history...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/history/predictions", params={"user_id": user_id}, headers=headers)
    print("Prediction history response:", response.status_code, response.json())

if __name__ == "__main__":
    register_user()
    token = login_user()

    # Предположим, что user_id = 1 (или нужно взять из БД)
    user_id = 1

    deposit(token, user_id)
    predict(token, user_id)

    print("[+] Waiting for worker to process the task...")
    time.sleep(10)  # Ждём пока воркер обработает

    get_predictions(token, user_id)
