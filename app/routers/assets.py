from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models import Asset, Relationship
from app.schemas import AssetCreate, AssetUpdate, AssetResponse
from app.auth import verify_api_key
from app.services.asset_service import (
    create_asset_service,
    import_assets_service
)
router = APIRouter(
    prefix="/assets",
    tags=["Assets"]
)


@router.post(
    "",
    response_model=AssetResponse,
    dependencies=[Depends(verify_api_key)]
)
def create_asset(
    asset: AssetCreate,
    db: Session = Depends(get_db)
):
    return create_asset_service(asset, db)


@router.get(
    "",
    response_model=list[AssetResponse]
)
def get_assets(
    type: str | None = None,
    status: str | None = None,
    tag: str | None = None,
    search: str | None = None,
    sort: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(Asset)

    if type:
        query = query.filter(
            Asset.type == type
        )

    if status:
        query = query.filter(
            Asset.status == status
        )

    if tag:
        query = query.filter(
            Asset.tags.contains([tag])
        )

    if search:
        query = query.filter(
            or_(
                Asset.value.ilike(f"%{search}%"),
                Asset.type.ilike(f"%{search}%"),
                Asset.status.ilike(f"%{search}%")
            )
        )

    ALLOWED_SORTS = {
        "last_seen": Asset.last_seen,
        "first_seen": Asset.first_seen,
        "type": Asset.type,
        "status": Asset.status,
    }

    if sort:
        if sort not in ALLOWED_SORTS:
            raise HTTPException(
                status_code=400,
                detail="Invalid sort field"
            )

        query = query.order_by(ALLOWED_SORTS[sort].desc())

    if size > 100:
        size = 100

    offset = (page - 1) * size

    assets = (
        query
        .offset(offset)
        .limit(size)
        .all()
    )

    return assets


@router.get(
    "/{asset_id}",
    response_model=AssetResponse
)
def get_asset(
    asset_id: str,
    db: Session = Depends(get_db)
):
    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id)
        .first()
    )

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    return asset


@router.put(
    "/{asset_id}",
    response_model=AssetResponse,
    dependencies=[Depends(verify_api_key)]
)
def update_asset(
    asset_id: str,
    asset_update: AssetUpdate,
    db: Session = Depends(get_db)
):
    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id)
        .first()
    )

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    update_data = asset_update.model_dump(
        exclude_unset=True
    )

    for key, value in update_data.items():
        setattr(asset, key, value)

    db.commit()
    db.refresh(asset)

    return asset


@router.delete(
    "/{asset_id}",
    dependencies=[Depends(verify_api_key)]
)
def delete_asset(
    asset_id: str,
    db: Session = Depends(get_db)
):
    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id)
        .first()
    )

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    db.delete(asset)
    db.commit()

    return {
        "message": "Asset deleted successfully"
    }

@router.post(
    "/import",
    dependencies=[Depends(verify_api_key)]
)
def import_assets(
    assets: list[AssetCreate],
    db: Session = Depends(get_db)
):
    return import_assets_service(
        assets,
        db
    )

@router.post(
    "/{asset_id}/stale",
    response_model=AssetResponse,
    dependencies=[Depends(verify_api_key)]
)
def mark_asset_stale(
    asset_id: str,
    db: Session = Depends(get_db)
):
    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id)
        .first()
    )

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    asset.status = "stale"

    db.commit()
    db.refresh(asset)

    return asset


@router.get("/{asset_id}/related")
def get_related_assets(
    asset_id: str,
    db: Session = Depends(get_db)
):
    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id)
        .first()
    )

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    relationships = (
        db.query(Relationship)
        .filter(
            (Relationship.source_asset_id == asset_id)
            |
            (Relationship.target_asset_id == asset_id)
        )
        .all()
    )

    related_ids = set()

    for relationship in relationships:

        if relationship.source_asset_id == asset_id:
            related_ids.add(
                relationship.target_asset_id
            )
        else:
            related_ids.add(
                relationship.source_asset_id
            )

    related_assets = (
        db.query(Asset)
        .filter(
            Asset.id.in_(related_ids)
        )
        .all()
    )

    return {
        "asset": asset,
        "related_assets": related_assets
    }

@router.post(
    "/import",
    dependencies=[Depends(verify_api_key)]
)
def import_assets(
    assets: list[AssetCreate],
    db: Session = Depends(get_db)
):
    imported = 0
    skipped = 0

    for asset in assets:
        try:
            create_asset_service(asset, db)
            imported += 1
        except HTTPException as e:
            if e.status_code == 409:
                skipped += 1
            else:
                raise e

    return {
        "imported": imported,
        "skipped": skipped
    }