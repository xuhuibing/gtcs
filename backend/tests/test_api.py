"""GTCS API 基础测试"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_login():
    resp = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_fail():
    resp = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "wrong",
    })
    assert resp.status_code == 401


def test_register():
    import random
    suffix = random.randint(10000, 99999)
    resp = client.post("/api/v1/auth/register", json={
        "username": f"test_user_{suffix}",
        "password": "test123",
        "display_name": "Test User",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "viewer"  # 注册角色固定为 viewer


def test_tariff_countries():
    resp = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123",
    })
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/v1/tariff/countries", headers=headers)
    assert resp.status_code == 200
    countries = resp.json()
    assert isinstance(countries, list)
    iso2s = [c["iso2"] for c in countries]
    assert "US" in iso2s
    for c in countries:
        if c["iso2"] == "US":
            assert c["line_count"] > 0


def test_tariff_browse():
    resp = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123",
    })
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/v1/tariff/browse?country=US&page=1&page_size=10", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["country"] == "US"
    assert len(data["items"]) > 0
    assert "local_code" in data["items"][0]


def test_tariff_lookup():
    resp = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123",
    })
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get(
        "/api/v1/tariff/lookup?hs_code=8528420000&dest_country=US&origin_country=CN",
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["hs_code"] == "8528420000"
    assert data["country"] == "US"


def test_tariff_search():
    resp = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123",
    })
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/v1/tariff/search?q=8528&country=US&limit=5", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


def test_auth_required():
    """Verify non-auth routes require authentication"""
    resp = client.get("/api/v1/tariff/countries")
    assert resp.status_code == 401  # 未登录应被拒


def test_docs_public():
    """Swagger docs should be publicly accessible"""
    resp = client.get("/docs")
    assert resp.status_code in (200, 307)  # May redirect
