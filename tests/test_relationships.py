from tests.conftest import client, headers, create_asset
import uuid


def test_relationship_graph():

    asset1 = {
        "type": "domain",
        "value": f"{uuid.uuid4().hex}.com",
        "source": "scanner",
        "status": "active",
        "tags": [],
        "metadata_json": {}
    }

    asset2 = {
        "type": "ip_address",
        "value": f"192.168.{uuid.uuid4().int % 255}.{uuid.uuid4().int % 255}",
        "source": "scanner",
        "status": "active",
        "tags": [],
        "metadata_json": {}
    }

    response1 = create_asset(asset1)
    response2 = create_asset(asset2)

    asset1_id = response1.json()["id"]
    asset2_id = response2.json()["id"]

    relationship = {
        "source_asset_id": asset1_id,
        "target_asset_id": asset2_id,
        "relationship_type": "resolves_to"
    }

    relationship_response = client.post(
        "/relationships",
        json=relationship,
        headers=headers   
    )
    assert relationship_response.status_code in [200, 201]

    graph = client.get(f"/assets/{asset1_id}/related")

    assert graph.status_code == 200

    data = graph.json()

    assert data["asset"]["id"] == asset1_id
    assert len(data["related_assets"]) == 1
    assert data["related_assets"][0]["id"] == asset2_id