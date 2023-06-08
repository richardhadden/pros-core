import pytest
from fastapi.testclient import TestClient
from httpx import Response as HttpxResponse
from pros_core.auth import LoggedInUser, User
from pros_core.setup_app import setup_app
from testing_app.app.core.config import settings
from tests.testing_app.app.main import app
from tests.utils import LoggedInClient

setup_app(app, settings)


@app.get("/currentUser/")
def get_current_user(user: User = LoggedInUser) -> User:
    return user


@pytest.fixture
def logged_in_client() -> LoggedInClient:
    client = TestClient(app)
    response = client.post(
        "/login/", data={"username": "johndoe", "password": "secret"}
    )
    access_token = response.json()["access_token"]
    client = LoggedInClient(app, access_token=access_token)
    return client


def test_api():
    client = TestClient(app)
    response = client.get("/")
    assert response.json() == "pros_core app created!"


def test_a_random_url_path_exists():
    assert app.url_path_for("Animal.list") == "/entities/animal/"


def test_login():
    """Manually test loggin in"""

    client = TestClient(app)
    response = client.post(
        "/login/", data={"username": "johndoe", "password": "secret"}
    )
    assert "access_token" in response.json()
    access_token = response.json()["access_token"]

    response = client.get(
        "/currentUser/", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.json() == {
        "disabled": False,
        "email": "johndoe@example.com",
        "full_name": "John Doe",
        "username": "johndoe",
    }


def test_logged_in_client_fixture(logged_in_client: LoggedInClient):
    # Test that a normal client cannot access the protect route
    client = TestClient(app)
    response = client.get("/currentUser/")
    assert response.status_code == 401

    # Now test that the logged_in_client can
    response = logged_in_client.get("/currentUser/")
    assert response.status_code == 200
    assert response.json() == {
        "disabled": False,
        "email": "johndoe@example.com",
        "full_name": "John Doe",
        "username": "johndoe",
    }
