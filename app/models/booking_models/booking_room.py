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
    ForeignKey,
    Numeric,
    UniqueConstraint,
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

if TYPE_CHECKING:
    from app.models.booking_models.booking import Booking
    from app.models.rooms_models.room import Room


# ============================================================
# Booking Room Model
# ============================================================

class BookingRoom(BaseTable):
    """
    Represents a room reserved as part of a booking.

    Stores the assigned room along with a pricing snapshot
    captured at the time of booking.
    """

    __tablename__ = "booking_rooms"

    __table_args__ = (
        UniqueConstraint(
            "booking_id",
            "room_id",
            name="uq_booking_room",
        ),
    )

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
    # Room Reference
    # ============================================================

    room_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "rooms.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    # ============================================================
    # Pricing Snapshot
    # ============================================================

    price_per_night: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    number_of_nights: Mapped[int] = mapped_column(
        nullable=False,
    )

    room_total: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    # ============================================================
    # Relationships
    # ============================================================

    booking: Mapped["Booking"] = relationship(
        back_populates="booking_rooms",
        foreign_keys=[booking_id],
    )

    room: Mapped["Room"] = relationship(
        foreign_keys=[room_id],
    )