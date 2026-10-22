from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_frontend_homepage_is_served() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Authorization Regression Lab" in response.text
    assert 'id="identity"' in response.text


def test_frontend_stylesheet_is_served() -> None:
    response = client.get("/static/style.css")

    assert response.status_code == 200
    assert ".response-panel" in response.text


def test_frontend_javascript_is_served() -> None:
    response = client.get("/static/app.js")

    assert response.status_code == 200
    assert "fetch(" in response.text
    assert "Authorization" in response.text
