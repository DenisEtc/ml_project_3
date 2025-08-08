import os
import uuid
import requests
import pytest

# Если тесты запускаются из контейнера tests в docker-compose — оставь по умолчанию:
# API_BASE_URL=http://ml_app:8000
# Если запускаешь pytest на хосте (Mac), приложение проброшено на 8000:
# API_BASE_URL=http://localhost:8000
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def unique_user():
    suf = uuid.uuid4().hex[:8]
    return {
        "username": f"test_user_{suf}",
        "email": f"test_user_{suf}@example.com",
        "password": "test123"
    }


def register_user(user):
    # Регистрируем как JSON
    resp = requests.post(f"{BASE_URL}/register", json=user, timeout=10)
    assert resp.status_code == 200, f"Register failed: {resp.status_code} {resp.text}"
    return resp.json()  # объект пользователя


def login_user(user):
    # /token ожидает форму (OAuth2PasswordRequestForm), шлём form-data
    data = {"username": user["username"], "password": user["password"]}
    resp = requests.post(f"{BASE_URL}/token", data=data, timeout=10)
    assert resp.status_code == 200, f"Login failed: {resp.status_code} {resp.text}"
    token = resp.json()["access_token"]
    return token


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
def test_register_login_me_and_transactions_flow():
    user = unique_user()
    created = register_user(user)
    assert created["username"] == user["username"]
    assert created["email"] == user["email"]
    assert "id" in created
    assert "balance" in created

    token = login_user(user)
    headers = auth_headers(token)

    # /users/me
    me = requests.get(f"{BASE_URL}/users/me", headers=headers, timeout=10)
    assert me.status_code == 200, me.text
    me_json = me.json()
    assert me_json["username"] == user["username"]
    user_id = me_json["id"]

    # депозит
    deposit = requests.post(
        f"{BASE_URL}/transactions",
        json={"user_id": user_id, "amount": 100.0, "type": "deposit"},
        headers=headers,
        timeout=10
    )
    assert deposit.status_code == 200, deposit.text
    dep_json = deposit.json()
    assert dep_json["amount"] == 100.0
    assert dep_json["type"] == "deposit"
    assert dep_json["user_id"] == user_id

    # списание
    withdraw = requests.post(
        f"{BASE_URL}/transactions",
        json={"user_id": user_id, "amount": 30.0, "type": "withdraw"},
        headers=headers,
        timeout=10
    )
    assert withdraw.status_code == 200, withdraw.text
    w_json = withdraw.json()
    assert w_json["amount"] == 30.0
    assert w_json["type"] == "withdraw"
    assert w_json["user_id"] == user_id

    # список транзакций
    txs = requests.get(f"{BASE_URL}/transactions/{user_id}", headers=headers, timeout=10)
    assert txs.status_code == 200, txs.text
    tx_list = txs.json()
    assert isinstance(tx_list, list)
    assert len(tx_list) >= 2


@pytest.mark.integration
def test_negative_amount_validation():
    user = unique_user()
    register_user(user)
    token = login_user(user)
    headers = auth_headers(token)

    me = requests.get(f"{BASE_URL}/users/me", headers=headers, timeout=10)
    assert me.status_code == 200
    user_id = me.json()["id"]

    # отрицательная сумма — должно быть 400 (или 422, если у тебя своя валидация)
    bad = requests.post(
        f"{BASE_URL}/transactions",
        json={"user_id": user_id, "amount": -50.0, "type": "deposit"},
        headers=headers,
        timeout=10
    )
    assert bad.status_code in (400, 422), bad.text


@pytest.mark.integration
def test_wrong_password_login():
    user = unique_user()
    register_user(user)

    # неверный пароль -> ожидаем 400 (у нас так реализовано) или 401
    resp = requests.post(
        f"{BASE_URL}/token",
        data={"username": user["username"], "password": "WRONG_PASS"},
        timeout=10
    )
    assert resp.status_code in (400, 401), resp.text
