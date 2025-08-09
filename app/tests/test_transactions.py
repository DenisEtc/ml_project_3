import os
import uuid
import requests
import pytest

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

def unique_user():
    suf = uuid.uuid4().hex[:8]
    return {
        "username": f"u_{suf}",
        "email": f"u_{suf}@ex.com",
        "password": "test123"
    }

def login(user):
    r = requests.post(f"{BASE_URL}/token", data={"username": user["username"], "password": user["password"]}, timeout=10)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]

@pytest.mark.integration
def test_deposit_withdraw_and_history():
    user = unique_user()
    assert requests.post(f"{BASE_URL}/register", json=user, timeout=10).status_code == 200
    token = login(user)
    headers = {"Authorization": f"Bearer {token}"}
    me = requests.get(f"{BASE_URL}/users/me", headers=headers, timeout=10).json()
    uid = me["id"]

    # депозит
    dep = requests.post(f"{BASE_URL}/transactions", json={"user_id": uid, "amount": 150.0, "type": "deposit"}, headers=headers, timeout=10)
    assert dep.status_code == 200, dep.text

    # списание
    wd = requests.post(f"{BASE_URL}/transactions", json={"user_id": uid, "amount": 50.0, "type": "withdraw"}, headers=headers, timeout=10)
    assert wd.status_code == 200, wd.text

    # история
    txs = requests.get(f"{BASE_URL}/transactions/{uid}", headers=headers, timeout=10)
    assert txs.status_code == 200, txs.text
    assert isinstance(txs.json(), list) and len(txs.json()) >= 2

@pytest.mark.integration
def test_negative_amount_and_overwithdraw():
    user = unique_user()
    assert requests.post(f"{BASE_URL}/register", json=user, timeout=10).status_code == 200
    token = login(user)
    headers = {"Authorization": f"Bearer {token}"}
    uid = requests.get(f"{BASE_URL}/users/me", headers=headers, timeout=10).json()["id"]

    # отрицательная сумма
    bad = requests.post(f"{BASE_URL}/transactions", json={"user_id": uid, "amount": -1.0, "type": "deposit"}, headers=headers, timeout=10)
    assert bad.status_code in (400, 422)

    # попытка списания без достаточного баланса
    over = requests.post(f"{BASE_URL}/transactions", json={"user_id": uid, "amount": 9999.0, "type": "withdraw"}, headers=headers, timeout=10)
    assert over.status_code in (400, 422)

@pytest.mark.integration
def test_transactions_forbidden_other_user():
    u1 = unique_user(); u2 = unique_user()
    assert requests.post(f"{BASE_URL}/register", json=u1, timeout=10).status_code == 200
    assert requests.post(f"{BASE_URL}/register", json=u2, timeout=10).status_code == 200
    t2 = login(u2)
    headers2 = {"Authorization": f"Bearer {t2}"}
    uid1 = requests.post(f"{BASE_URL}/token", data={"username": u1["username"], "password": u1["password"]}, timeout=10)
    assert uid1.status_code == 200
    me1 = requests.get(f"{BASE_URL}/users/me", headers={"Authorization": f"Bearer {uid1.json()['access_token']}"}, timeout=10).json()
    # u2 пытается запросить историю u1
    res = requests.get(f"{BASE_URL}/transactions/{me1['id']}", headers=headers2, timeout=10)
    assert res.status_code == 403
