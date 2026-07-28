# ============================================================
# Standard Library
# ============================================================

from typing import TYPE_CHECKING
from uuid import UUID

# ============================================================
# Third Party
# ============================================================

from sqlalchemy import (
    Enum,
    ForeignKey,
    Text,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

# ============================================================
# Local Imports
# ============================================================

from app.database.base_table import BaseTable

from app.common.enums.booking_enums.booking_enums import (
    BookingStatus,
)

if TYPE_CHECKING:
    from app.models.booking_models.booking import Booking
    from app.models.users_models.users import User


# ============================================================
# Booking History Model
# ============================================================

class BookingHistory(BaseTable):
    """
    Stores every booking status transition.
    """

    __tablename__ = "booking_history"

    # ============================================================
    # Booking Reference
    # ============================================================

    booking_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "bookings.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # ============================================================
    # Status Transition
    # ============================================================

    old_status: Mapped[BookingStatus] = mapped_column(
        Enum(
            BookingStatus,
            name="booking_status_enum",
        ),
        nullable=False,
    )

    new_status: Mapped[BookingStatus] = mapped_column(
        Enum(
            BookingStatus,
            name="booking_status_enum",
        ),
        nullable=False,
    )

    # ============================================================
    # Audit Information
    # ============================================================

    changed_by: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    # ============================================================
    # Remarks
    # ============================================================

    remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ============================================================
    # Relationships
    # ============================================================

    booking: Mapped["Booking"] = relationship(
        back_populates="booking_history",
    )

    changed_by_user: Mapped["User | None"] = relationship(
        foreign_keys=[changed_by],
    )