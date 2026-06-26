from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Asset
from app.schemas import ImportResponse, ImportAsset
from datetime import datetime
from typing import List


router = APIRouter(
    prefix="/import",
    tags=["Import"]
)

@router.post(
    "",
    response_model=ImportResponse
)
def import_assets(
    assets: list[ImportAsset],
    db: Session = Depends(get_db)
):

    imported = 0
    updated = 0
    failed = 0

    for asset in assets:
        try:
            
            existing_asset = (
                db.query(Asset)
                .filter(
                    Asset.type == asset.type,
                    Asset.value == asset.value
                )
                .first()
            )

            if not existing_asset:

                new_asset = Asset(
                    type=asset.type,
                    value=asset.value,
                    status=asset.status,
                    source=asset.source,
                    tags=asset.tags,
                    metadata_json=asset.metadata_json
                )

                db.add(new_asset)

                imported += 1

            else:
                existing_asset.last_seen = datetime.utcnow()

                if existing_asset.status == "stale":
                    existing_asset.status = "active"

                # Merge tags
                existing_asset.tags = list(
                    set(existing_asset.tags + asset.tags)
                )

                # Merge metadata
                existing_asset.metadata_json={
                    **existing_asset.metadata_json,
                    **asset.metadata_json
                }

                updated += 1
                    
        except Exception:
            failed += 1
    db.commit()

    return {
        "imported": imported,
        "updated": updated,
        "failed": failed
    }