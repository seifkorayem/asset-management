from sqlalchemy import Column, String, DateTime, UniqueConstraint, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base
from datetime import datetime, UTC
import uuid

class Asset(Base):
    __tablename__ = "assets"

    __table_args__ = (
        UniqueConstraint(
            "type",
            "value",
            name="uq_asset_type_value"
        ),
    )

    id = Column(String,primary_key=True, default=lambda: str(uuid.uuid4()))

    type = Column(
        String,
        nullable=False,
        index=True
    )

    value = Column(
        String,
        nullable=False,
        index=True
    )

    status = Column(
        String,
        default="active",
        index=True
    )

    source = Column(String)

    first_seen = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC)
    )

    last_seen = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        index=True
    )

    tags = Column(
        JSONB,
        default=list
    )

    metadata_json = Column(
        JSONB,
        default=dict
    )

class Relationship(Base):
    __tablename__ = "relationships"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    source_asset_id = Column(
        String,
        ForeignKey("assets.id"),
        nullable=False,
        index=True
    )

    target_asset_id = Column(
        String,
        ForeignKey("assets.id"),
        nullable=False,
        index=True
)

    relationship_type = Column(
        String,
        nullable=False,
        index=True
    )