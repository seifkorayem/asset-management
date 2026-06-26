from tests.conftest import client, headers, create_asset
import uuid

def test_asset_deduplication():
    asset = {
        "type": "domain",
        "value": f"{uuid.uuid4().hex}.com",
        "source": "scanner",
        "status": "active",
        "tags": ["production"],
        "metadata_json": {}
    }

    first = client.post(
        "/assets",
        json=asset,
        headers=headers
    )
    assert first.status_code in [200, 201]

    second = client.post(
        "/assets",
        json=asset,
        headers=headers
    )
    assert second.status_code == 409

def test_filter_by_type():

    asset = {
        "type": "service",
        "value": f"{uuid.uuid4().hex}.service",
        "source": "scanner",
        "status": "active",
        "tags": ["backend"],
        "metadata_json": {}
    }

    create_asset(asset)

    response = client.get(
        "/assets?type=service"
    )

    assert response.status_code == 200

    assets = response.json()

    assert any(
        a["type"] == "service"
        for a in assets
    )

def test_filter_by_status():

    asset = {
        "type": "domain",
        "value": f"{uuid.uuid4().hex}.com",
        "source": "scanner",
        "status": "stale",
        "tags": [],
        "metadata_json": {}
    }

    create_asset(asset)

    response = client.get("/assets?status=stale")

    assert response.status_code == 200

    assets = response.json()

    assert any(
        a["status"] == "stale"
        for a in assets
    )

def test_filter_by_tag():

    asset = {
        "type": "domain",
        "value": f"{uuid.uuid4().hex}.com",
        "source": "scanner",
        "status": "active",
        "tags": ["production"],
        "metadata_json": {}
    }

    create_asset(asset)

    response = client.get("/assets?tag=production")

    assert response.status_code == 200

    assets = response.json()

    assert any(
        "production" in a["tags"]
        for a in assets
    )

def test_search_assets():

    unique = uuid.uuid4().hex

    asset = {
        "type": "domain",
        "value": f"{unique}.com",
        "source": "scanner",
        "status": "active",
        "tags": [],
        "metadata_json": {}
    }

    create_asset(asset)

    response = client.get(f"/assets?search={unique}")

    assert response.status_code == 200

    assets = response.json()

    assert any(
        unique in a["value"]
        for a in assets
    )