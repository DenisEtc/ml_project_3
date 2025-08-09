import os
import uuid
import requests
import pytest

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

@pytest.mark.integration
def test_predict_and_history_with_test_mode():
    # Ожидаем, что APP запущен с TEST_MODE=1 (см. docker-compose.yml)
    assert os.getenv("TEST_MODE") in (None, "1")  # локально может быть не задано, в compose мы зададим

    # регистрируем и логинимся
    suf = uuid.uuid4().hex[:8]
    user = {"username": f"p_{suf}", "email": f"p_{suf}@ex.com", "password": "test123"}
    assert requests.post(f"{BASE_URL}/register", json=user, timeout=10).status_code == 200
    tok = requests.post(f"{BASE_URL}/token", data={"username": user["username"], "password": user["password"]}, timeout=10)
    assert tok.status_code == 200
    access = tok.json()["access_token"]
    headers = {"Authorization": f"Bearer {access}"}
    uid = requests.get(f"{BASE_URL}/users/me", headers=headers, timeout=10).json()["id"]

    # отправляем predict — в TEST_MODE он должен сразу записать Prediction в БД без очереди
    req = {
        "user_id": uid,
        "model_id": 1,
        "input_data": {"feature1": 1.0, "feature2": 2.0}
    }
    p = requests.post(f"{BASE_URL}/predict", json=req, headers=headers, timeout=10)
    assert p.status_code == 200, p.text
    assert "message" in p.json()

    # получаем историю предсказаний
    hist = requests.get(f"{BASE_URL}/predictions/{uid}", headers=headers, timeout=10)
    assert hist.status_code == 200, hist.text
    items = hist.json()
    assert isinstance(items, list) and len(items) >= 1
    latest = items[0]
    assert latest["user_id"] == uid
    assert latest["model_id"] == 1
    assert "prediction" in latest

@pytest.mark.integration
def test_predict_forbidden_other_user():
    # user A
    s1 = uuid.uuid4().hex[:8]
    u1 = {"username": f"a_{s1}", "email": f"a_{s1}@ex.com", "password": "test123"}
    assert requests.post(f"{BASE_URL}/register", json=u1, timeout=10).status_code == 200
    t1 = requests.post(f"{BASE_URL}/token", data={"username": u1["username"], "password": u1["password"]}, timeout=10)
    h1 = {"Authorization": f"Bearer {t1.json()['access_token']}"}
    uid1 = requests.get(f"{BASE_URL}/users/me", headers=h1, timeout=10).json()["id"]

    # user B
    s2 = uuid.uuid4().hex[:8]
    u2 = {"username": f"b_{s2}", "email": f"b_{s2}@ex.com", "password": "test123"}
    assert requests.post(f"{BASE_URL}/register", json=u2, timeout=10).status_code == 200
    t2 = requests.post(f"{BASE_URL}/token", data={"username": u2["username"], "password": u2["password"]}, timeout=10)
    h2 = {"Authorization": f"Bearer {t2.json()['access_token']}"}
    uid2 = requests.get(f"{BASE_URL}/users/me", headers=h2, timeout=10).json()["id"]

    # u2 пытается отправить предикт от имени u1 -> 403
    bad = requests.post(
        f"{BASE_URL}/predict",
        json={"user_id": uid1, "model_id": 1, "input_data": {"x": 1}},
        headers=h2,
        timeout=10
    )
    assert bad.status_code == 403
