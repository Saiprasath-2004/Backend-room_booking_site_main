# ============================================================
# Standard Library
# ============================================================

from datetime import (
    datetime,
    timezone,
)

import uuid

from uuid import UUID

# ============================================================
# Third Party
# ============================================================

from sqlalchemy.ext.asyncio import AsyncSession

# ============================================================
# Local Imports
# ============================================================

# Repository
from app.models.booking_models.booking_history import BookingHistory
from app.repositories.payment_repositories.payment_repository import (
    PaymentRepository,
)

# Schemas
from app.schema.payment_schema.payment_schemas import (
    CompletePaymentRequest,
    CreatePaymentRequest,
    InvoiceResponse,
    PaymentFailureRequest,
    PaymentGatewayResponse,
    PaymentMessageResponse,
    PaymentResponse,
    PaymentSummaryResponse,
    RevenueSummaryResponse,
)

# Payment Exceptions
from app.exceptions.payment_exceptions.payment_exceptions import (
    BookingPaymentAlreadyExistsException,
    InvoiceNotFoundException,
    InvalidPaymentStatusException,
    PaymentAccessDeniedException,
    PaymentAlreadyCompletedException,
    PaymentAlreadyFailedException,
    PaymentNotFoundException,
)

# Booking Exceptions
from app.exceptions.booking_exceptions.booking_exceptions import (
    BookingNotFoundException,
)

# Booking Enums
from app.common.enums.booking_enums.booking_enums import (
    BookingStatus,
    PaymentStatus as BookingPaymentStatus,
)
# Payment Enums
from app.common.enums.payment_enums.payment_enums import (
    InvoiceStatus,
    PaymentStatus as PaymentTransactionStatus,
)



from app.models.payment_models.invoice import (
    Invoice,
)

from app.models.payment_models.payment import (
    Payment,
)

from app.models.users_models.users import (
    User,
)


# ============================================================
# Payment Service
# ============================================================

class PaymentService:

    def __init__(
        self,
        db: AsyncSession,
    ):

        self.db = db

        self.repository = PaymentRepository(
            db,
        )

    # ============================================================
    # Private Helper Methods
    # ============================================================

    async def generate_payment_reference(
        self,
    ) -> str:
        """
        Generates a unique payment reference.
        """

        return (
            f"PAY-{uuid.uuid4().hex[:12].upper()}"
        )


    async def generate_gateway_order_id(
        self,
    ) -> str:
        """
        Generates a mock payment gateway order ID.
        """

        return (
            f"ORDER-{uuid.uuid4().hex[:12].upper()}"
        )


    async def generate_invoice_number(
        self,
    ) -> str:
        """
        Generates a unique invoice number.
        """

        return (
            f"INV-{uuid.uuid4().hex[:12].upper()}"
        )


    # ============================================================
    # Create Payment
    # ============================================================

    async def create_payment(
        self,
        request: CreatePaymentRequest,
        current_user: User,
    ) -> PaymentGatewayResponse:
        """
        Creates a payment request for a booking.
        """

        # ------------------------------------------------------------
        # Validate Booking
        # ------------------------------------------------------------

        booking = await self.repository.get_booking_by_id(
            request.booking_id,
        )

        if booking is None:
            raise BookingNotFoundException()

        if booking.customer_id != current_user.id:
            raise PaymentAccessDeniedException()

        if booking.booking_status != BookingStatus.PENDING:
            raise InvalidPaymentStatusException()

        # ------------------------------------------------------------
        # Check Existing Payment
        # ------------------------------------------------------------

        existing_payment = (
            await self.repository.get_payment_by_booking_id(
                booking.id,
            )
        )

        if existing_payment is not None:
            raise BookingPaymentAlreadyExistsException()

        # ------------------------------------------------------------
        # Generate Payment Details
        # ------------------------------------------------------------

        payment_reference = (
            await self.generate_payment_reference()
        )

        gateway_order_id = (
            await self.generate_gateway_order_id()
        )

        # ------------------------------------------------------------
        # Create Payment
        # ------------------------------------------------------------

        payment = Payment(
            booking_id=booking.id,
            user_id=current_user.id,
            payment_reference=payment_reference,
            gateway_order_id=gateway_order_id,
            amount=booking.total_amount,
            currency="INR",
            payment_method=request.payment_method,
            payment_gateway=request.payment_gateway,
            payment_status=PaymentTransactionStatus.PENDING,
            created_by=current_user.email,
            updated_by=current_user.email,
        )

        # ------------------------------------------------------------
        # Save Payment
        # ------------------------------------------------------------

        try:

            payment = await self.repository.create_payment(
                payment,
            )

            await self.db.commit()

        except Exception:

            await self.db.rollback()

            raise

        # ------------------------------------------------------------
        # Return Gateway Details
        # ------------------------------------------------------------

        return PaymentGatewayResponse(
            payment_reference=payment.payment_reference,
            gateway_order_id=payment.gateway_order_id,
            payment_status=payment.payment_status,
        )


    # ============================================================
    # Complete Payment
    # ============================================================

    async def complete_payment(
        self,
        request: CompletePaymentRequest,
        current_user: User,
    ) -> PaymentResponse:
        """
        Completes a pending payment after successful gateway payment.
        """

        try:

            # ------------------------------------------------------------
            # Retrieve Payment
            # ------------------------------------------------------------

            payment = await self.repository.get_payment_by_reference(
                request.payment_reference,
            )

            if payment is None:
                raise PaymentNotFoundException()

            # ------------------------------------------------------------
            # Validate Ownership
            # ------------------------------------------------------------

            if payment.user_id != current_user.id:
                raise PaymentAccessDeniedException()

            # ------------------------------------------------------------
            # Validate Payment Status
            # ------------------------------------------------------------

            if (
                payment.payment_status
                == PaymentTransactionStatus.SUCCESS
            ):
                raise PaymentAlreadyCompletedException()

            if (
                payment.payment_status
                == PaymentTransactionStatus.FAILED
            ):
                raise PaymentAlreadyFailedException()

            # ------------------------------------------------------------
            # Retrieve Booking
            # ------------------------------------------------------------

            booking = payment.booking

            if booking is None:
                raise BookingNotFoundException()

            previous_booking_status = booking.booking_status

            # ------------------------------------------------------------
            # Complete Payment
            # ------------------------------------------------------------

            payment.payment_status = (
                PaymentTransactionStatus.SUCCESS
            )

            payment.gateway_payment_id = (
                request.gateway_payment_id
            )

            payment.gateway_response = (
                request.gateway_response
            )

            payment.paid_at = datetime.now(
                timezone.utc,
            )

            payment.updated_by = current_user.email

            # ------------------------------------------------------------
            # Update Booking
            # ------------------------------------------------------------

            booking.payment_status = (
                BookingPaymentStatus.SUCCESS
            )

            booking.booking_status = (
                BookingStatus.CONFIRMED
            )

            booking.updated_by = current_user.email

            # ------------------------------------------------------------
            # Create Booking History
            # ------------------------------------------------------------

            booking_history = BookingHistory(

                booking_id=booking.id,

                old_status=previous_booking_status,

                new_status=BookingStatus.CONFIRMED,

                changed_by=current_user.id,

                remarks="Payment completed successfully.",

                created_by=current_user.email,

                updated_by=current_user.email,

            )

            await self.repository.create_booking_history(
                booking_history,
            )

            # ------------------------------------------------------------
            # Generate Invoice
            # ------------------------------------------------------------

            invoice = Invoice(

                booking_id=booking.id,

                invoice_number=await self.generate_invoice_number(),

                invoice_status=InvoiceStatus.GENERATED,

                invoice_amount=payment.amount,

                currency=payment.currency,

                generated_at=datetime.now(
                    timezone.utc,
                ),

                created_by=current_user.email,

                updated_by=current_user.email,

            )

            await self.repository.create_invoice(
                invoice,
            )

            # ------------------------------------------------------------
            # Update Payment
            # ------------------------------------------------------------

            payment = await self.repository.update_payment(
                payment,
            )

            # ------------------------------------------------------------
            # Commit Transaction
            # ------------------------------------------------------------

            await self.db.commit()

            await self.db.refresh(
                payment,
            )

            await self.db.refresh(
                booking,
            )

            # ------------------------------------------------------------
            # Return Response
            # ------------------------------------------------------------

            return PaymentResponse(

                id=payment.id,

                booking_id=payment.booking_id,

                payment_reference=payment.payment_reference,

                amount=payment.amount,

                currency=payment.currency,

                payment_method=payment.payment_method,

                payment_gateway=payment.payment_gateway,

                payment_status=payment.payment_status,

                gateway_order_id=payment.gateway_order_id,

                gateway_payment_id=payment.gateway_payment_id,

                paid_at=payment.paid_at,

                created_at=payment.created_at,

            )

        except Exception:

            await self.db.rollback()

            raise

    # ============================================================
    # Fail Payment
    # ============================================================

    async def fail_payment(
        self,
        request: PaymentFailureRequest,
        current_user: User,
    ) -> PaymentMessageResponse:
        """
        Marks a pending payment as failed.
        """

        try:

            # ------------------------------------------------------------
            # Retrieve Payment
            # ------------------------------------------------------------

            payment = await self.repository.get_payment_by_reference(
                request.payment_reference,
            )

            if payment is None:
                raise PaymentNotFoundException()

            # ------------------------------------------------------------
            # Validate Ownership
            # ------------------------------------------------------------

            if payment.user_id != current_user.id:
                raise PaymentAccessDeniedException()

            # ------------------------------------------------------------
            # Validate Payment Status
            # ------------------------------------------------------------

            if (
                payment.payment_status
                == PaymentTransactionStatus.SUCCESS
            ):
                raise PaymentAlreadyCompletedException()

            if (
                payment.payment_status
                == PaymentTransactionStatus.FAILED
            ):
                raise PaymentAlreadyFailedException()

            # ------------------------------------------------------------
            # Update Payment
            # ------------------------------------------------------------

            payment.payment_status = (
                PaymentTransactionStatus.FAILED
            )

            payment.failure_reason = (
                request.failure_reason
            )

            payment.gateway_response = (
                request.gateway_response
            )

            payment.updated_by = current_user.email

            # ------------------------------------------------------------
            # Save Changes
            # ------------------------------------------------------------

            payment = await self.repository.update_payment(
                payment,
            )

            # ------------------------------------------------------------
            # Commit Transaction
            # ------------------------------------------------------------

            await self.db.commit()

            await self.db.refresh(
                payment,
            )

            # ------------------------------------------------------------
            # Return Response
            # ------------------------------------------------------------

            return PaymentMessageResponse(
                message="Payment marked as failed successfully.",
            )

        except Exception:

            await self.db.rollback()

            raise


    # ============================================================
    # Get Payment By ID
    # ============================================================

    async def get_payment_by_id(
        self,
        payment_id: UUID,
        current_user: User,
    ) -> PaymentResponse:
        """
        Retrieve a payment by its ID.
        """

        payment = await self.repository.get_payment_by_id(
            payment_id,
        )

        if payment is None:
            raise PaymentNotFoundException()

        if payment.user_id != current_user.id:
            raise PaymentAccessDeniedException()

        return PaymentResponse(

            id=payment.id,

            booking_id=payment.booking_id,

            payment_reference=payment.payment_reference,

            amount=payment.amount,

            currency=payment.currency,

            payment_method=payment.payment_method,

            payment_gateway=payment.payment_gateway,

            payment_status=payment.payment_status,

            gateway_order_id=payment.gateway_order_id,

            gateway_payment_id=payment.gateway_payment_id,

            paid_at=payment.paid_at,

            created_at=payment.created_at,

        )

    # ============================================================
    # Get Payment By Reference
    # ============================================================

    async def get_payment_by_reference(
        self,
        payment_reference: str,
        current_user: User,
    ) -> PaymentResponse:
        """
        Retrieve a payment using its payment reference.
        """

        payment = await self.repository.get_payment_by_reference(
            payment_reference,
        )

        if payment is None:
            raise PaymentNotFoundException()

        if payment.user_id != current_user.id:
            raise PaymentAccessDeniedException()

        return PaymentResponse(

            id=payment.id,

            booking_id=payment.booking_id,

            payment_reference=payment.payment_reference,

            amount=payment.amount,

            currency=payment.currency,

            payment_method=payment.payment_method,

            payment_gateway=payment.payment_gateway,

            payment_status=payment.payment_status,

            gateway_order_id=payment.gateway_order_id,

            gateway_payment_id=payment.gateway_payment_id,

            paid_at=payment.paid_at,

            created_at=payment.created_at,

        )

    # ============================================================
    # Get Invoice By Booking
    # ============================================================

    async def get_invoice_by_booking(
        self,
        booking_id: UUID,
        current_user: User,
    ) -> InvoiceResponse:
        """
        Retrieve the invoice associated with a booking.
        """

        # ------------------------------------------------------------
        # Retrieve Invoice
        # ------------------------------------------------------------

        invoice = await self.repository.get_invoice_by_booking_id(
            booking_id,
        )

        if invoice is None:
            raise InvoiceNotFoundException()

        # ------------------------------------------------------------
        # Validate Booking
        # ------------------------------------------------------------

        booking = invoice.booking

        if booking is None:
            raise BookingNotFoundException()

        # ------------------------------------------------------------
        # Validate Ownership
        # ------------------------------------------------------------

        if booking.user_id != current_user.id:
            raise PaymentAccessDeniedException()

        # ------------------------------------------------------------
        # Return Response
        # ------------------------------------------------------------

        return InvoiceResponse(

            id=invoice.id,

            booking_id=invoice.booking_id,

            invoice_number=invoice.invoice_number,

            invoice_status=invoice.invoice_status,

            invoice_amount=invoice.invoice_amount,

            currency=invoice.currency,

            generated_at=invoice.generated_at,

            created_at=invoice.created_at,

        )

    # ============================================================
    # Get My Payments
    # ============================================================

    async def get_my_payments(
        self,
        current_user: User,
    ) -> list[PaymentSummaryResponse]:
        """
        Retrieve all payments made by the current user.
        """

        payments = await self.repository.get_my_payments(
            current_user.id,
        )

        return [

            PaymentSummaryResponse(

                id=payment.id,

                booking_id=payment.booking_id,

                payment_reference=payment.payment_reference,

                amount=payment.amount,

                currency=payment.currency,

                payment_method=payment.payment_method,

                payment_gateway=payment.payment_gateway,

                payment_status=payment.payment_status,

                paid_at=payment.paid_at,

                created_at=payment.created_at,

            )

            for payment in payments

        ]

    # ============================================================
    # Get Property Payments
    # ============================================================

    async def get_property_payments(
        self,
        current_user: User,
    ) -> list[PaymentSummaryResponse]:
        """
        Retrieve all payments received for the current owner's properties.
        """

        payments = await self.repository.get_property_payments(
            current_user.id,
        )

        return [

            PaymentSummaryResponse(

                id=payment.id,

                booking_id=payment.booking_id,

                payment_reference=payment.payment_reference,

                amount=payment.amount,

                currency=payment.currency,

                payment_method=payment.payment_method,

                payment_gateway=payment.payment_gateway,

                payment_status=payment.payment_status,

                paid_at=payment.paid_at,

                created_at=payment.created_at,

            )

            for payment in payments

        ]

    # ============================================================
    # Get Revenue Summary
    # ============================================================

    async def get_revenue_summary(
        self,
        current_user: User,
    ) -> RevenueSummaryResponse:
        """
        Retrieve the revenue summary for the current property owner.
        """

        summary = await self.repository.get_revenue_summary(
            current_user.id,
        )

        return RevenueSummaryResponse(

            total_payments=summary["total_payments"],

            total_revenue=summary["total_revenue"],

            average_payment_amount=summary[
                "average_payment_amount"
            ],

        )