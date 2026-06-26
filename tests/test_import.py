from tests.conftest import client, headers
import uuid

def test_import_assets():
    payload = [
        {
            "type": "domain",
            "value": "example.com",
            "source": "scanner",
            "status": "active",
            "tags": [],
            "metadata_json": {}
        },
        {
            "type": "ip_address",
            "value": "8.8.8.8",
            "source": "scanner",
            "status": "active",
            "tags": [],
            "metadata_json": {}
        }
    ]

    response = client.post(
        "/assets/import",
        json=payload,
        headers=headers
    )

    assert response.status_code == 200

def test_import_deduplicates_assets():

    payload = [
        {
            "type": "domain",
            "value": "duplicate.com",
            "source": "scanner",
            "status": "active",
            "tags": [],
            "metadata_json": {}
        },
        {
            "type": "domain",
            "value": "duplicate.com",
            "source": "scanner",
            "status": "active",
            "tags": [],
            "metadata_json": {}
        }
    ]

    response = client.post(
        "/assets/import",
        json=payload,
        headers=headers
    )

    assert response.status_code == 200

    assets = client.get("/assets?search=duplicate.com")

    assert len(assets.json()) == 1

def test_import_invalid_asset():

    payload = [
        {
            "type": "invalid_type",
            "value": "abc",
            "source": "scanner"
        }
    ]

    response = client.post(
        "/assets/import",
        json=payload,
        headers=headers
    )

    assert response.status_code == 422