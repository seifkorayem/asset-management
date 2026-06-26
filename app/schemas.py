from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Any, Dict, List, Annotated, Optional
from datetime import datetime
from enum import Enum
import ipaddress
import re

class AssetType(str, Enum):
    domain = "domain"
    subdomain = "subdomain"
    ip_address = "ip_address"
    service = "service"
    certificate = "certificate"
    technology = "technology"

class AssetStatus(str, Enum):
    active = "active"
    stale = "stale"
    archived = "archived"

class ImportAsset(BaseModel):
    type: AssetType
    value: str
    source: str
    status: AssetStatus = AssetStatus.active
    tags: List[str] = []
    metadata_json: Dict[str, Any] = {}

Tag = Annotated[str, Field(min_length=1, max_length=50)]

class AssetCreate(BaseModel):
    type: AssetType
    value: str = Field(
        min_length=1,
        max_length=255
    )
    source: str = Field(
        min_length=1,
        max_length=100
    )
    status: AssetStatus = AssetStatus.active
    tags: List[Tag] = Field(default_factory=list)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_asset(self):
        self.value = self.value.strip()
        self.source = self.source.strip()

        # Remove duplicate tags while preserving order
        self.tags = list(dict.fromkeys(tag.strip() for tag in self.tags))

        if self.type == AssetType.ip_address:
            try:
                ipaddress.ip_address(self.value)
            except ValueError:
                raise ValueError("Invalid IP address.")

        elif self.type in (
            AssetType.domain,
            AssetType.subdomain,
        ):
            domain_pattern = (
                r"^(?!-)(?:[A-Za-z0-9-]{1,63}\.)+[A-Za-z]{2,63}$"
            )

            if not re.fullmatch(domain_pattern, self.value):
                raise ValueError("Invalid domain or subdomain.")

        return self

    model_config = {
        "json_schema_extra": {
            "example": {
                "type": "domain",
                "value": "google.com",
                "source": "security_scan",
                "status": "active",
                "tags": [
                    "production",
                    "internet-facing"
                ],
                "metadata_json": {
                    "owner": "security_team"
                }
            }
        }
    }

class AssetUpdate(BaseModel):
    value: Optional[str] = None

    status: Optional[AssetStatus] = None

    source: Optional[str] = None

    tags: Optional[List[str]] = None

    metadata_json: Optional[Dict[str, Any]] = None

class AssetResponse(BaseModel):
    id: str

    type: AssetType

    value: str

    status: AssetStatus

    source: Optional[str]

    first_seen: datetime

    last_seen: datetime

    tags: List[str]

    metadata_json: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)



class RelationshipCreate(BaseModel):
    source_asset_id: str

    target_asset_id: str

    relationship_type: str

class RelationshipResponse(RelationshipCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str

class ImportResponse(BaseModel):
    imported: int

    updated: int

    failed: int

    errors: List[dict] = Field(default_factory=list)

class AIQueryRequest(BaseModel):
    query: str

class SearchRequest(BaseModel):
    query: str


class AssetFilter(BaseModel):
    type: Optional[str] = None
    status: Optional[str] = None
    tag: Optional[str] = None


class AssetSummaryResponse(BaseModel):
    summary: str