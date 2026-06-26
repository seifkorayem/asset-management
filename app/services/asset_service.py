from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.logger import logger
from app.models import Asset
from app.schemas import AssetCreate, AssetUpdate
from app.services.ai_service import AI_CACHE


def clear_asset_cache(asset_id: str):
    """
    Remove cached AI responses for an asset.
    """
    AI_CACHE.pop(f"risk:{asset_id}", None)
    AI_CACHE.pop(f"category:{asset_id}", None)


def create_asset_service(
    asset: AssetCreate,
    db: Session
):
    logger.info(
        "Creating asset (%s): %s",
        asset.type,
        asset.value
    )

    existing_asset = (
        db.query(Asset)
        .filter(
            Asset.type == asset.type,
            Asset.value == asset.value
        )
        .first()
    )

    if existing_asset:
        logger.warning(
            "Duplicate asset detected (%s): %s",
            asset.type,
            asset.value
        )

        raise HTTPException(
            status_code=409,
            detail="Asset already exists"
        )

    try:
        new_asset = Asset(
            type=asset.type,
            value=asset.value,
            status=asset.status,
            source=asset.source,
            tags=asset.tags,
            metadata_json=asset.metadata_json
        )

        db.add(new_asset)
        db.commit()
        db.refresh(new_asset)

        logger.info(
            "Asset created successfully (%s)",
            new_asset.id
        )

        return new_asset

    except SQLAlchemyError:
        db.rollback()

        logger.exception(
            "Database error while creating asset"
        )

        raise HTTPException(
            status_code=500,
            detail="Database error"
        )


def get_asset_service(
    asset_id: str,
    db: Session
):
    logger.info(
        "Fetching asset %s",
        asset_id
    )

    asset = (
        db.query(Asset)
        .filter(
            Asset.id == asset_id
        )
        .first()
    )

    if not asset:
        logger.warning(
            "Asset not found (%s)",
            asset_id
        )

        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    return asset


def import_assets_service(
    assets: list[AssetCreate],
    db: Session
):
    logger.info(
        "Starting asset import (%d assets)",
        len(assets)
    )

    imported = 0
    skipped = 0

    for asset in assets:

        try:
            create_asset_service(
                asset,
                db
            )
            imported += 1

        except HTTPException as e:

            if e.status_code == 409:
                skipped += 1
            else:
                raise

    logger.info(
        "Import finished. Imported=%d Skipped=%d",
        imported,
        skipped
    )

    return {
        "imported": imported,
        "skipped": skipped
    }


def update_asset_service(
    asset_id: str,
    asset_update: AssetUpdate,
    db: Session
):
    logger.info(
        "Updating asset %s",
        asset_id
    )

    asset = get_asset_service(
        asset_id,
        db
    )

    update_data = asset_update.model_dump(
        exclude_unset=True
    )

    for key, value in update_data.items():
        setattr(asset, key, value)

    try:
        db.commit()

        clear_asset_cache(asset_id)

        db.refresh(asset)

        logger.info(
            "Asset updated successfully (%s)",
            asset_id
        )

        return asset

    except SQLAlchemyError:
        db.rollback()

        logger.exception(
            "Database error while updating asset %s",
            asset_id
        )

        raise HTTPException(
            status_code=500,
            detail="Database error"
        )


def delete_asset_service(
    asset_id: str,
    db: Session
):
    logger.info(
        "Deleting asset %s",
        asset_id
    )

    asset = get_asset_service(
        asset_id,
        db
    )

    try:
        db.delete(asset)
        db.commit()

        clear_asset_cache(asset_id)

        logger.info(
            "Asset deleted successfully (%s)",
            asset_id
        )

        return {
            "message": "Asset deleted successfully"
        }

    except SQLAlchemyError:
        db.rollback()

        logger.exception(
            "Database error while deleting asset %s",
            asset_id
        )

        raise HTTPException(
            status_code=500,
            detail="Database error"
        )


def mark_asset_stale_service(
    asset_id: str,
    db: Session
):
    logger.info(
        "Marking asset %s as stale",
        asset_id
    )

    asset = get_asset_service(
        asset_id,
        db
    )

    asset.status = "stale"

    try:
        db.commit()

        clear_asset_cache(asset_id)

        db.refresh(asset)

        logger.info(
            "Asset marked as stale (%s)",
            asset_id
        )

        return asset

    except SQLAlchemyError:
        db.rollback()

        logger.exception(
            "Database error while marking asset stale %s",
            asset_id
        )

        raise HTTPException(
            status_code=500,
            detail="Database error"
        )