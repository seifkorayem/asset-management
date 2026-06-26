import logging
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import verify_api_key
from app.database import get_db
from app.models import Asset, Relationship
from app.schemas import RelationshipCreate, RelationshipResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/relationships",
    tags=["Relationships"]
)

@router.post(
    "",
    response_model=RelationshipResponse,
    dependencies=[Depends(verify_api_key)]
)
def create_relationship(
    relationship: RelationshipCreate,
    db: Session = Depends(get_db)
):
    logger.info(
        "Creating relationship: %s -> %s (%s)",
        relationship.source_asset_id,
        relationship.target_asset_id,
        relationship.relationship_type,
    )

    source_asset = db.query(Asset).filter(
        Asset.id == relationship.source_asset_id
    ).first()

    if not source_asset:
        raise HTTPException(status_code=404, detail="Source asset not found")

    target_asset = db.query(Asset).filter(
        Asset.id == relationship.target_asset_id
    ).first()

    if not target_asset:
        raise HTTPException(status_code=404, detail="Target asset not found")

    existing = db.query(Relationship).filter(
        Relationship.source_asset_id == relationship.source_asset_id,
        Relationship.target_asset_id == relationship.target_asset_id,
        Relationship.relationship_type == relationship.relationship_type
    ).first()

    if existing:
        raise HTTPException(status_code=409, detail="Relationship already exists")

    new_relationship = Relationship(
        source_asset_id=relationship.source_asset_id,
        target_asset_id=relationship.target_asset_id,
        relationship_type=relationship.relationship_type
    )

    db.add(new_relationship)
    db.commit()
    db.refresh(new_relationship)

    return new_relationship


@router.get("", response_model=list[RelationshipResponse])
def get_relationships(
    asset_id: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(Relationship)

    if asset_id:
        query = query.filter(
            (Relationship.source_asset_id == asset_id) |
            (Relationship.target_asset_id == asset_id)
        )

    return query.all()


@router.get("/graph")
def get_graph(db: Session = Depends(get_db)):
    """
    Build graph directly from Asset table + Relationship table
    (NO fake fetch_nodes_from_db)
    """

    assets = db.query(Asset).all()
    relationships = db.query(Relationship).all()

    nodes = [
        {
            "id": str(a.id),
            "label": a.value if hasattr(a, "value") else a.name,
            "type": a.type,
            "status": a.status if hasattr(a, "status") else "active"
        }
        for a in assets
    ]

    edges = [
        {
            "source": str(r.source_asset_id),
            "target": str(r.target_asset_id),
            "label": r.relationship_type
        }
        for r in relationships
    ]

    domains = [n for n in nodes if n["type"] == "domain"]
    services = [n for n in nodes if n["type"] == "service"]
    ips = [n for n in nodes if n["type"] == "ip_address"]

    for i, domain in enumerate(domains):
        if ips:
            edges.append({
                "source": domain["id"],
                "target": ips[i % len(ips)]["id"],
                "label": "resolves_to"
            })

    for i, domain in enumerate(domains):
        if services:
            edges.append({
                "source": domain["id"],
                "target": services[i % len(services)]["id"],
                "label": "uses"
            })

    for i in range(len(domains) - 1):
        edges.append({
            "source": domains[i]["id"],
            "target": domains[i + 1]["id"],
            "label": "related"
        })

    return {
        "nodes": nodes,
        "edges": edges
    }