"""Test API bằng chế độ demo (không cần mạng)."""
from fastapi.testclient import TestClient

from backend.app.main import build_providers, create_app

client = TestClient(create_app(build_providers(demo=True)))


def test_categories():
    data = client.get("/api/categories").json()
    ids = [c["id"] for c in data["categories"]]
    assert ids == ["vn", "crypto"]
    vn = data["categories"][0]
    assert "4h" not in vn["timeframes"] and "1d" in vn["timeframes"]


def test_list_and_search():
    vn = client.get("/api/assets/vn").json()["items"]
    assert any(a["symbol"] == "FPT" for a in vn)
    res = client.get("/api/search", params={"q": "hoa phat"}).json()["items"]
    assert res[0]["symbol"] == "HPG"
    res = client.get("/api/search", params={"q": "btc"}).json()["items"]
    assert res[0]["symbol"] == "BTCUSDT"


def test_candles_and_info():
    r = client.get("/api/assets/crypto/BTCUSDT/candles", params={"tf": "4h", "limit": 100})
    assert r.status_code == 200
    c = r.json()["candles"]
    assert len(c) == 100 and c[0]["time"] < c[-1]["time"]
    info = client.get("/api/assets/vn/FPT/info").json()
    assert info["currency"] == "VND" and info["fields"]


def test_errors():
    assert client.get("/api/assets/vn/FPT/candles", params={"tf": "4h"}).status_code == 400
    assert client.get("/api/assets/vn/NOPE/info").status_code == 404
    assert client.get("/api/assets/forex").status_code == 404
