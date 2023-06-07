from fastapi.testclient import TestClient
from pros_core.setup_app import setup_app
from testing_app.app.core.config import settings
from tests.testing_app.app.main import app

setup_app(app, settings)
client = TestClient(app)


def test_api():
    response = client.get("/")
    assert response.json() == "pros_core app created!"


def test_a_random_url_path_exists():
    assert app.url_path_for("Animal.list") == "/entities/animal/"
