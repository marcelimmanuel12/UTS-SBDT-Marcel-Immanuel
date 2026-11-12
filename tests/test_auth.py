"""Uji unit permintaan tanpa akses JWT; tidak memerlukan server atau database."""
from fastapi.testclient import TestClient
from app.main import app


def test_unauthorized_post_blocked():
    client = TestClient(app)
    response = client.post("/predict", json={
        "transaction_amount": 5000, "transactions_24h": 1, "new_device": False
    })
    assert response.status_code == 401


def test_health():
    client = TestClient(app)
    assert client.get("/health").json()["status"] == "ok"
