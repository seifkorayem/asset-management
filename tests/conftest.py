from fastapi.testclient import TestClient
from app.main import app
import os

client = TestClient(app)

headers = {
    "X-API-Key": os.getenv("API_KEY")
}


def create_asset(asset):
    response = client.post(
        "/assets",
        json=asset,
        headers=headers
    )

    assert response.status_code in [200, 201]

    return response