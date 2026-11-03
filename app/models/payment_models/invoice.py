# ============================================================
# Standard Library
# ============================================================

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

# ============================================================
# Third Party
# ============================================================

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
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

from app.common.enums.payment_enums.payment_enums import (
    InvoiceStatus,
)

if TYPE_CHECKING:
    from app.models.booking_models.booking import Booking


# ============================================================
# Invoice Model
# ============================================================

class Invoice(BaseTable):
    """
    Represents the invoice generated for a successful booking payment.
    """

    __tablename__ = "invoices"

    __table_args__ = (

        UniqueConstraint(
            "invoice_number",
            name="uq_invoice_number",
        ),

        CheckConstraint(
            "invoice_amount > 0",
            name="ck_invoice_amount_positive",
        ),

    )

    # ============================================================
    # Foreign Key
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
    # Invoice Information
    # ============================================================

    invoice_number: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        unique=True,
        index=True,
    )

    invoice_status: Mapped[InvoiceStatus] = mapped_column(
        Enum(
            InvoiceStatus,
            name="invoice_status_enum",
        ),
        nullable=False,
        default=InvoiceStatus.GENERATED,
    )

    invoice_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="INR",
    )

    # ============================================================
    # Invoice Timestamp
    # ============================================================

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # ============================================================
    # Relationships
    # ============================================================

    booking: Mapped["Booking"] = relationship(
        back_populates="invoice",
    )