# ============================================================
# Standard Library
# ============================================================

from datetime import datetime
from uuid import UUID, uuid4

# ============================================================
# Third Party
# ============================================================

from sqlalchemy import (
    DateTime,
    func,
    String,
)

from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

# ============================================================
# Local Imports
# ============================================================

from app.database.base import Base


class BaseTable(Base):
    """
    Abstract base model inherited by all database tables.

    Provides:
    - UUID Primary Key
    - Audit Information
    - Created Timestamp
    - Updated Timestamp
    """

    __abstract__ = True

    # ============================================================
    # Primary Key
    # ============================================================

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # ============================================================
    # Audit Fields
    # ============================================================

    created_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    updated_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # ============================================================
    # Timestamps
    # ============================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )