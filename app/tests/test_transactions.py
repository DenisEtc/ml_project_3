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
    assert requests.post(f"{BASE_URL}/register", json=user, timeout=10).status_code == 200
    t = requests.post(f"{BASE_URL}/token", data={"username": user["username"], "password": user["password"]}, timeout=10)
    assert t.status_code == 200
    return t.json()["access_token"]

@pytest.mark.integration
def test_deposit_and_list():
    user = unique_user()
    token = login(user)
    headers = {"Authorization": f"Bearer {token}"}
    me = requests.get(f"{BASE_URL}/users/me", headers=headers, timeout=10).json()
    res = requests.post(f"{BASE_URL}/transactions/deposit", json={"user_id": me["id"], "amount": 50, "type": "deposit"}, headers=headers, timeout=10)
    assert res.status_code == 200, res.text
    lst = requests.get(f"{BASE_URL}/transactions/{me['id']}", headers=headers, timeout=10)
    assert lst.status_code == 200
    assert any(tx["type"] == "deposit" and tx["amount"] >= 50 for tx in lst.json())

@pytest.mark.integration
def test_transactions_forbidden_other_user():
    u1 = unique_user(); u2 = unique_user()
    assert requests.post(f"{BASE_URL}/register", json=u1, timeout=10).status_code == 200
    assert requests.post(f"{BASE_URL}/register", json=u2, timeout=10).status_code == 200
    t2 = requests.post(f"{BASE_URL}/token", data={"username": u2["username"], "password": u2["password"]}, timeout=10)
    headers2 = {"Authorization": f"Bearer {t2.json()['access_token']}"}
    t1 = requests.post(f"{BASE_URL}/token", data={"username": u1["username"], "password": u1["password"]}, timeout=10)
    assert t1.status_code == 200
    me1 = requests.get(f"{BASE_URL}/users/me", headers={"Authorization": f"Bearer {t1.json()['access_token']}"}, timeout=10).json()
    res = requests.get(f"{BASE_URL}/transactions/{me1['id']}", headers=headers2, timeout=10)
    assert res.status_code == 403
