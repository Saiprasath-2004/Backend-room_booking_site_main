# ============================================================
# Standard Library
# ============================================================

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

# ============================================================
# Third Party
# ============================================================

from sqlalchemy import (
    CheckConstraint,
    Date,
    Enum,
    ForeignKey,
    Numeric,
    String,
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
    PaymentStatus,
)

if TYPE_CHECKING:
    from app.models.users_models.users import User
    from app.models.property_models.property import Property
    from app.models.booking_models.booking_room import BookingRoom
    from app.models.booking_models.booking_history import BookingHistory
    from app.models.booking_models.booking_cancellation import BookingCancellation
    from app.models.payment_models.payment import Payment
    from app.models.payment_models.invoice import Invoice
    from app.models.review_models.review_model import Review


# ============================================================
# Booking Model
# ============================================================

class Booking(BaseTable):
    """
    Represents a hotel booking made by a customer.
    """

    __tablename__ = "bookings"

    __table_args__ = (
        CheckConstraint(
            "adult_count > 0",
            name="ck_booking_adult_count",
        ),
        CheckConstraint(
            "child_count >= 0",
            name="ck_booking_child_count",
        ),
    )

    # ============================================================
    # Booking Ownership
    # ============================================================

    customer_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    property_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "properties.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    booking_reference: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
        index=True,
    )

    # ============================================================
    # Stay Information
    # ============================================================

    check_in_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    check_out_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # ============================================================
    # Guest Information
    # ============================================================

    adult_count: Mapped[int] = mapped_column(
        nullable=False,
    )

    child_count: Mapped[int] = mapped_column(
        nullable=False,
    )

    # ============================================================
    # Financial Information
    # ============================================================

    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    # ============================================================
    # Booking Status
    # ============================================================

    booking_status: Mapped[BookingStatus] = mapped_column(
        Enum(
            BookingStatus,
            name="booking_status_enum",
        ),
        nullable=False,
        default=BookingStatus.PENDING,
        index=True,
    )

    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(
            PaymentStatus,
            name="payment_status_enum",
        ),
        nullable=False,
        default=PaymentStatus.PENDING,
        index=True,
    )

    # ============================================================
    # Customer Notes
    # ============================================================

    special_requests: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ============================================================
    # Relationships
    # ============================================================

    customer: Mapped["User"] = relationship(
        foreign_keys=[customer_id],
        
    )

    property: Mapped["Property"] = relationship(
        foreign_keys=[property_id],
        
    )

    booking_rooms: Mapped[list["BookingRoom"]] = relationship(
        back_populates="booking",
        cascade="all, delete-orphan",
        
    )

    booking_history: Mapped[list["BookingHistory"]] = relationship(
        back_populates="booking",
        cascade="all, delete-orphan",
        
    )

    payments: Mapped[list["Payment"]] = relationship(
        back_populates="booking",
        cascade="all, delete-orphan",
        
    )

    invoice: Mapped["Invoice | None"] = relationship(
        back_populates="booking",
        uselist=False,
        cascade="all, delete-orphan",
        
    )

    cancellation: Mapped["BookingCancellation | None"] = relationship(
        back_populates="booking",
        uselist=False,
        cascade="all, delete-orphan",
    )

    review: Mapped["Review | None"] = relationship(
        back_populates="booking",
        uselist=False,

    )