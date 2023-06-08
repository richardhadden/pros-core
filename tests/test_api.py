import pytest
from fastapi.testclient import TestClient
from httpx import Response as HttpxResponse
from pros_core.auth import LoggedInUser
from pros_core.setup_app import setup_app
from testing_app.app.core.config import settings
from tests.testing_app.app.main import app

setup_app(app, settings)


# For testing auth, throw in a protected route
@app.get("/protected/")
def protected(user=LoggedInUser) -> str:
    return "Got a protected thing"


class LoggedInClient(TestClient):
    """Subclass of TestClient to automatically include the access token
    into the header of any request"""

    def __init__(self, app, access_token: str, *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self._access_token = access_token

    def get(self, *args, **kwargs) -> HttpxResponse:
        return super().get(
            *args,
            **kwargs,
            headers={
                "Authorization": f"Bearer {self._access_token}",
                **kwargs.get("headers", {}),
            },
        )

    def post(self, *args, **kwargs) -> HttpxResponse:
        return super().post(
            *args,
            **kwargs,
            headers={
                "Authorization": f"Bearer {self._access_token}",
                **kwargs.get("headers", {}),
            },
        )

    def put(self, *args, **kwargs) -> HttpxResponse:
        return super().put(
            *args,
            **kwargs,
            headers={
                "Authorization": f"Bearer {self._access_token}",
                **kwargs.get("headers", {}),
            },
        )

    def patch(self, *args, **kwargs) -> HttpxResponse:
        return super().patch(
            *args,
            **kwargs,
            headers={
                "Authorization": f"Bearer {self._access_token}",
                **kwargs.get("headers", {}),
            },
        )

    def delete(self, *args, **kwargs) -> HttpxResponse:
        return super().delete(
            *args,
            **kwargs,
            headers={
                "Authorization": f"Bearer {self._access_token}",
                **kwargs.get("headers", {}),
            },
        )


@pytest.fixture
def logged_in_client() -> LoggedInClient:
    client = TestClient(app)
    response = client.post(
        "/login/", data={"username": "johndoe@mail.com", "password": "hunter2"}
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
        "/login/", data={"username": "johndoe@mail.com", "password": "hunter2"}
    )
    assert "access_token" in response.json()
    access_token = response.json()["access_token"]

    response = client.get(
        "/protected/", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.json() == "Got a protected thing"


def test_logged_in_client_fixture(logged_in_client: LoggedInClient):
    # Test that a normal client cannot access the protect route
    client = TestClient(app)
    response = client.get("/protected/")
    assert response.status_code == 401

    # Now test that the logged_in_client can
    response = logged_in_client.get("/protected/")
    assert response.status_code == 200
    assert response.json() == "Got a protected thing"
