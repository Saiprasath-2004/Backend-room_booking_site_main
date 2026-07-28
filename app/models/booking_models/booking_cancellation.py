# ============================================================
# Standard Library
# ============================================================

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

# ============================================================
# Third Party
# ============================================================

from sqlalchemy import (
    Enum,
    ForeignKey,
    Numeric,
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
    CancellationType,
    RefundStatus,
)

if TYPE_CHECKING:
    from app.models.booking_models.booking import Booking
    from app.models.users_models.users import User


# ============================================================
# Booking Cancellation Model
# ============================================================

class BookingCancellation(BaseTable):
    """
    Stores cancellation information for cancelled bookings.
    """

    __tablename__ = "booking_cancellations"

    # ============================================================
    # Booking Reference
    # ============================================================

    booking_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "bookings.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    # ============================================================
    # Cancellation Information
    # ============================================================

    cancellation_type: Mapped[CancellationType] = mapped_column(
        Enum(
            CancellationType,
            name="cancellation_type_enum",
        ),
        nullable=False,
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # ============================================================
    # Refund Information
    # ============================================================

    refund_status: Mapped[RefundStatus] = mapped_column(
        Enum(
            RefundStatus,
            name="refund_status_enum",
        ),
        nullable=False,
        default=RefundStatus.NOT_APPLICABLE,
    )

    refund_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # ============================================================
    # Cancelled By
    # ============================================================

    cancelled_by: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    # ============================================================
    # Relationships
    # ============================================================

    booking: Mapped["Booking"] = relationship(
        back_populates="cancellation",
    )

    cancelled_by_user: Mapped["User | None"] = relationship(
        foreign_keys=[cancelled_by],
    )