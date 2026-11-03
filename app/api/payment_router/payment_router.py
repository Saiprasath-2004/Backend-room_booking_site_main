# ============================================================
# Standard Library
# ============================================================

from uuid import UUID

# ============================================================
# Third Party
# ============================================================

from fastapi import (
    APIRouter,
    Depends,
    status,
)

from sqlalchemy.ext.asyncio import AsyncSession

# ============================================================
# Local Imports
# ============================================================

from app.database.session import get_db

from app.dependencies.auth import get_current_user

from app.models.users_models.users import User

from app.services.payment_services.payment_service import (
    PaymentService,
)

from app.schema.payment_schema.payment_schemas import (
    CreatePaymentRequest,
    CompletePaymentRequest,
    PaymentFailureRequest,
    PaymentGatewayResponse,
    PaymentSummaryResponse,
    PaymentResponse,
    InvoiceResponse,
    RevenueSummaryResponse,
    PaymentMessageResponse,
)

# ============================================================
# Router
# ============================================================

router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)

# ============================================================
# Service Dependency
# ============================================================

def get_payment_service(
    db: AsyncSession = Depends(get_db),
) -> PaymentService:
    """
    Dependency that provides the PaymentService.
    """
    return PaymentService(db)


# ============================================================
# Create Payment
# ============================================================

@router.post(
    "",
    response_model=PaymentGatewayResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_payment(
    request: CreatePaymentRequest,
    current_user: User = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
) -> PaymentGatewayResponse:
    """
    Initiate a payment for an existing booking.
    """

    return await service.create_payment(
        request=request,
        current_user=current_user,
    )


# ============================================================
# Complete Payment
# ============================================================

@router.patch(
    "/complete",
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK,
)
async def complete_payment(
    request: CompletePaymentRequest,
    current_user: User = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
) -> PaymentResponse:
    """
    Complete a pending payment after successful gateway payment.
    """

    return await service.complete_payment(
        request=request,
        current_user=current_user,
    )

# ============================================================
# Fail Payment
# ============================================================

@router.patch(
    "/fail",
    response_model=PaymentMessageResponse,
    status_code=status.HTTP_200_OK,
)
async def fail_payment(
    request: PaymentFailureRequest,
    current_user: User = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
) -> PaymentMessageResponse:
    """
    Mark a pending payment as failed.
    """

    return await service.fail_payment(
        request=request,
        current_user=current_user,
    )


# ============================================================
# Get Payment By ID
# ============================================================

@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK,
)
async def get_payment_by_id(
    payment_id: UUID,
    current_user: User = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
) -> PaymentResponse:
    """
    Retrieve a payment using its unique payment ID.
    """

    return await service.get_payment_by_id(
        payment_id=payment_id,
        current_user=current_user,
    )


# ============================================================
# Get Payment By Reference
# ============================================================

@router.get(
    "/reference/{payment_reference}",
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK,
)
async def get_payment_by_reference(
    payment_reference: str,
    current_user: User = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
) -> PaymentResponse:
    """
    Retrieve a payment using its payment reference.
    """

    return await service.get_payment_by_reference(
        payment_reference=payment_reference,
        current_user=current_user,
    )


# ============================================================
# Get My Payments
# ============================================================

@router.get(
    "/me",
    response_model=list[PaymentSummaryResponse],
    status_code=status.HTTP_200_OK,
)
async def get_my_payments(
    current_user: User = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
) -> list[PaymentSummaryResponse]:
    """
    Retrieve all payments made by the authenticated customer.
    """

    return await service.get_my_payments(
        current_user=current_user,
    )


# ============================================================
# Get Invoice By Booking
# ============================================================

@router.get(
    "/{booking_id}/invoice",
    response_model=InvoiceResponse,
    status_code=status.HTTP_200_OK,
)
async def get_invoice_by_booking(
    booking_id: UUID,
    current_user: User = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
) -> InvoiceResponse:
    """
    Retrieve the invoice for a completed booking.
    """

    return await service.get_invoice_by_booking(
        booking_id=booking_id,
        current_user=current_user,
    )


# ============================================================
# Get Invoice By Booking
# ============================================================

@router.get(
    "/{booking_id}/invoice",
    response_model=InvoiceResponse,
    status_code=status.HTTP_200_OK,
)
async def get_invoice_by_booking(
    booking_id: UUID,
    current_user: User = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
) -> InvoiceResponse:
    """
    Retrieve the invoice for a completed booking.
    """

    return await service.get_invoice_by_booking(
        booking_id=booking_id,
        current_user=current_user,
    )


# ============================================================
# Get Revenue Summary
# ============================================================

@router.get(
    "/property/revenue",
    response_model=RevenueSummaryResponse,
    status_code=status.HTTP_200_OK,
)
async def get_revenue_summary(
    current_user: User = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
) -> RevenueSummaryResponse:
    """
    Retrieve the revenue summary for the authenticated property owner.
    """

    return await service.get_revenue_summary(
        current_user=current_user,
    )