# ============================================================
# Standard Library
# ============================================================

from uuid import UUID
from datetime import datetime
from decimal import Decimal
# ============================================================
# Third Party
# ============================================================

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

# ============================================================
# Local Imports
# ============================================================

from app.common.enums.payment_enums.payment_enums import (
    PaymentGateway,
    PaymentMethod,
    PaymentStatus,
    InvoiceStatus,
)

# ============================================================
# Create Payment Request
# ============================================================

class CreatePaymentRequest(BaseModel):
    """
    Request schema for initiating a payment
    for an existing booking.
    """

    booking_id: UUID

    payment_method: PaymentMethod

    payment_gateway: PaymentGateway

    model_config = ConfigDict(
        from_attributes=True,
    )


# ============================================================
# Complete Payment Request
# ============================================================
class CompletePaymentRequest(BaseModel):
    """
    Request schema used by the mock payment gateway
    to complete a payment successfully.
    """

    payment_reference: str = Field(
        min_length=1,
        max_length=255,
    )

    gateway_payment_id: str = Field(
        min_length=1,
        max_length=255,
    )

    gateway_response: str | None = Field(
        default=None,
        max_length=5000,
    )

    model_config = ConfigDict(
        from_attributes=True,
    )

# ============================================================
# Payment Failure Request
# ============================================================

class PaymentFailureRequest(BaseModel):
    """
    Request schema used by the mock payment gateway
    to simulate a failed payment.
    """

    failure_reason: str = Field(
        min_length=5,
        max_length=500,
    )

    gateway_response: str | None = Field(
        default=None,
        max_length=5000,
    )

    model_config = ConfigDict(
        from_attributes=True,
    )

# ============================================================
# Payment Gateway Response
# ============================================================

class PaymentGatewayResponse(BaseModel):
    """
    Response returned immediately after creating
    a payment through the mock gateway.
    """

    payment_reference: str

    gateway_order_id: str

    payment_status: PaymentStatus

    model_config = ConfigDict(
        from_attributes=True,
    )


# ============================================================
# Payment Summary Response
# ============================================================

class PaymentSummaryResponse(BaseModel):
    """
    Lightweight payment response used
    when listing payments.
    """

    id: UUID

    booking_id: UUID

    payment_reference: str

    amount: Decimal

    currency: str

    payment_method: PaymentMethod

    payment_gateway: PaymentGateway

    payment_status: PaymentStatus

    paid_at: datetime | None

    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


# ============================================================
# Revenue Summary Response
# ============================================================

class RevenueSummaryResponse(BaseModel):
    """
    Revenue summary for a property owner.
    """

    total_payments: int

    total_revenue: Decimal

    average_payment_amount: Decimal

    model_config = ConfigDict(
        from_attributes=True,
    )
    
# ============================================================
# Payment Response
# ============================================================

class PaymentResponse(BaseModel):
    """
    Detailed payment response.
    """

    id: UUID

    booking_id: UUID

    user_id: UUID

    payment_reference: str

    amount: Decimal

    currency: str

    payment_method: PaymentMethod

    payment_gateway: PaymentGateway

    payment_status: PaymentStatus

    gateway_order_id: str | None

    gateway_payment_id: str | None

    gateway_response: str | None

    failure_reason: str | None

    paid_at: datetime | None

    created_by: str | None

    updated_by: str | None

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


# ============================================================
# Invoice Response
# ============================================================

class InvoiceResponse(BaseModel):
    """
    Detailed invoice response.
    """

    id: UUID

    booking_id: UUID

    invoice_number: str

    invoice_status: InvoiceStatus

    invoice_amount: Decimal

    currency: str

    generated_at: datetime

    created_by: str | None

    updated_by: str | None

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


# ============================================================
# Payment Message Response
# ============================================================

class PaymentMessageResponse(BaseModel):
    """
    Generic success/message response
    for payment operations.
    """

    success: bool

    message: str