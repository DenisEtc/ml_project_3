import os
import uuid
import requests
import pytest

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

def unique_user():
    suf = uuid.uuid4().hex[:8]
    return {
        "username": f"test_user_{suf}",
        "email": f"test_user_{suf}@example.com",
        "password": "test123"
    }

@pytest.mark.integration
def test_register_and_me():
    user = unique_user()
    r = requests.post(f"{BASE_URL}/register", json=user, timeout=10)
    assert r.status_code == 200, r.text
    token = requests.post(f"{BASE_URL}/token", data={"username": user["username"], "password": user["password"]}, timeout=10)
    assert token.status_code == 200, token.text
    access = token.json()["access_token"]
    me = requests.get(f"{BASE_URL}/users/me", headers={"Authorization": f"Bearer {access}"}, timeout=10)
    assert me.status_code == 200, me.text
    assert me.json()["username"] == user["username"]

@pytest.mark.integration
def test_login_wrong_password():
    user = unique_user()
    assert requests.post(f"{BASE_URL}/register", json=user, timeout=10).status_code == 200
    bad = requests.post(f"{BASE_URL}/token", data={"username": user["username"], "password": "WRONG"}, timeout=10)
    assert bad.status_code in (400, 401)
