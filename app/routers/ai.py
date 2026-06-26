from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import Asset
from app.schemas import AIQueryRequest
from app.services.ai_service import (
    parse_query,
    generate_filters,
    summarize_assets,
    summarize_risk,
    categorize_asset,
    generate_report,
    generate_graph_relationships

)
from app.services.risk_service import calculate_asset_risk

from app.schemas import SearchRequest


class GraphRequest(BaseModel):
    assets: list[str]

router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)

@router.post("/query")
def ai_query(
    request: AIQueryRequest,
    db: Session = Depends(get_db)
):

    filters = parse_query(request.query)

    query = db.query(Asset)

    if "value" in filters:
        query = query.filter(
            Asset.value.ilike(f"%{filters['value']}%")
        )

    if "source" in filters:
        query = query.filter(
            Asset.source == filters["source"]
        )

    if "type" in filters:
        query = query.filter(
            Asset.type == filters["type"]
        )

    if "status" in filters:
        query = query.filter(
            Asset.status == filters["status"]
        )

    if "tag" in filters:
        query = query.filter(
            Asset.tags.contains([filters["tag"]])
        )

    return {
        "filters": filters,
        "results": query.all()
    }

@router.post("/risk/{asset_id}")
def calculate_risk(asset_id: str, db: Session = Depends(get_db)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    risk = calculate_asset_risk(asset)
    summary = summary = summarize_risk(
        asset.id,
        risk
    )

    return {
        "risk_score": risk["risk_score"],
        "summary": summary
    }

@router.post("/categorize/{asset_id}")
def categorize(asset_id: str, db: Session = Depends(get_db)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    result = categorize_asset(asset)

    return result

@router.post("/report")
def generate_security_report(
    db: Session = Depends(get_db)
):
    assets = db.query(Asset).all()

    total_assets = len(assets)
    expired_certificates = 0

    for asset in assets:
        if (
            asset.type == "certificate"
            and asset.status.lower() == "expired"
        ):
            expired_certificates += 1

    high_risk_assets = 0

    for asset in assets:
        risk = calculate_asset_risk(asset)

        if risk["risk_score"] >= 60:
            high_risk_assets += 1

    report = generate_report(
        total_assets=total_assets,
        expired_certificates=expired_certificates,
        high_risk_assets=high_risk_assets
    )

    return {
        "total_assets": total_assets,
        "expired_certificates": expired_certificates,
        "high_risk_assets": high_risk_assets,
        "recommendations": report.recommendations
    }

@router.post("/search")
def search_assets(
    request: SearchRequest,
    db: Session = Depends(get_db)
):

    filters = generate_filters(request.query)

    query = db.query(Asset)

    if filters.type:
        query = query.filter(
            Asset.type == filters.type
        )

    if filters.status:
        query = query.filter(
            Asset.status == filters.status
        )

    if filters.tag:
        query = query.filter(
            Asset.tags.contains([filters.tag])
        )

    assets = query.all()

    summary = summarize_assets(assets)

    return {
        "filters": filters,
        "count": len(assets),
        "assets": assets,
        "summary": summary.summary
    }

@router.post("/graph")
def generate_graph(request: GraphRequest):
    return generate_graph_relationships(request.assets)