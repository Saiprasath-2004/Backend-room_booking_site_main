# ============================================================
# Standard Library
# ============================================================

from uuid import UUID

# ============================================================
# Third Party
# ============================================================

from sqlalchemy import (
    func,
    select,
)

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import (
    joinedload,
)

from sqlalchemy.exc import SQLAlchemyError
# ============================================================
# Local Imports
# ============================================================

from app.common.enums.booking_enums.booking_enums import PaymentStatus
from app.models.booking_models.booking import Booking

from app.models.booking_models.booking_history import BookingHistory
from app.models.booking_models.booking_room import BookingRoom
from app.models.property_models.property import Property
from app.models.rooms_models.room import Room
from app.models.payment_models.payment import Payment
from app.models.payment_models.invoice import Invoice
# ============================================================
# Payment Repository
# ============================================================

class PaymentRepository:

    def __init__(
        self,
        db: AsyncSession,
    ):

        self.db = db

    # ============================================================
    # Booking Queries
    # ============================================================

    async def get_booking_by_id(
        self,
        booking_id: UUID,
    ) -> Booking | None:
        try:
            result = await self.db.execute(
                select(Booking)
                .options(
                    joinedload(Booking.booking_rooms)
                    .joinedload(BookingRoom.room)
                    .joinedload(Room.room_type),
                )
                .where(
                    Booking.id == booking_id,
                )
            )

            return result.unique().scalar_one_or_none()
        except SQLAlchemyError:
            raise

    # ============================================================
    # Payment Queries
    # ============================================================

    async def get_payment_by_reference(
        self,
        payment_id: UUID,
    ) -> Payment | None:
        try:
            result = await self.db.execute(
                select(Payment)
                .options(
                    joinedload(Payment.booking),
                )
                .where(
                    Payment.id == payment_id,
                )
            )

            return result.scalar_one_or_none()

        except SQLAlchemyError:
            raise
    
    async def get_payment_by_reference(
        self,
        payment_reference: str,
    ) -> Payment | None:
        try:
            result = await self.db.execute(
                select(Payment)
                .options(
                    joinedload(Payment.booking),
                )
                .where(
                    Payment.payment_reference == payment_reference,
                )
            )

            return result.scalar_one_or_none()
        except SQLAlchemyError:
            raise

    async def get_payment_by_booking_id(
        self,
        booking_id: UUID,
    ) -> Payment | None:
        try:
            result = await self.db.execute(
                select(Payment)
                .options(
                    joinedload(Payment.booking),
                )
                .where(
                    Payment.booking_id == booking_id,
                )
            )

            return result.scalar_one_or_none()

        except SQLAlchemyError:
            raise
    
    async def get_invoice_by_booking_id(
        self,
        booking_id: UUID,
    ) -> Invoice | None:

        try:
            result = await self.db.execute(
                select(Invoice)
                .options(
                    joinedload(Invoice.booking),
                )
                .where(
                    Invoice.booking_id == booking_id,
                )
            )

            return result.scalar_one_or_none()

        except SQLAlchemyError:
            raise

    # ============================================================
    # Invoice Queries
    # ============================================================

    async def get_invoice_by_id(
        self,
        invoice_id: UUID,
    ) -> Invoice | None:

        try:

            result = await self.db.execute(
                select(Invoice)
                .options(
                    joinedload(Invoice.booking),
                )
                .where(
                    Invoice.id == invoice_id,
                )   
            )

            return result.scalar_one_or_none()

        except SQLAlchemyError:
            raise
    # ============================================================
    # Payment Commands
    # ============================================================

    async def create_payment(
        self,
        payment: Payment,
    ) -> Payment:

        try:
            self.db.add(
                payment,
            )

            await self.db.flush()

            await self.db.refresh(
                payment,
            )

            return payment

        except SQLAlchemyError:
            await self.db.rollback()
            raise

    # ============================================================
    # Invoice Commands
    # ============================================================

    async def create_invoice(
        self,
        invoice: Invoice,
    ) -> Invoice:
        try:
            self.db.add(
                invoice,
            )

            await self.db.flush()

            await self.db.refresh(
                invoice,
            )

            return invoice
        except SQLAlchemyError:
            await self.db.rollback()
            raise
    # ============================================================
    # Payment Commands
    # ============================================================

    async def update_payment(
        self,
        payment: Payment,
    ) -> Payment:
        try:
            await self.db.flush()

            await self.db.refresh(
                payment,
            )

            return payment
        except SQLAlchemyError:
            await self.db.rollback()
            raise


    # ============================================================
    # Payment Queries
    # ============================================================

    async def get_my_payments(
        self,
        customer_id: UUID,
    ) -> list[Payment]:

        result = await self.db.execute(
            select(Payment)
            .options(
                joinedload(Payment.booking),
            )
            .join(
                Booking,
                Booking.id == Payment.booking_id,
            )
            .where(
                Booking.customer_id == customer_id,
            )
            .order_by(
                Payment.created_at.desc(),
            )
        )

        return list(
            result.scalars().all(),
        )

    # ============================================================
    # Property Payment Queries
    # ============================================================

    async def get_property_payments(
        self,
        owner_id: UUID,
    ) -> list[Payment]:
        try:
            result = await self.db.execute(
                select(Payment)
                .options(
                    joinedload(Payment.booking),
                )
                .join(
                    Booking,
                    Booking.id == Payment.booking_id,
                )
                .join(
                    Property,
                    Property.id == Booking.property_id,
                )
                .where(
                    Property.owner_id == owner_id,
                )
                .order_by(
                    Payment.created_at.desc(),
                )
            )

            return list(
                result.scalars().all(),
            )
        except SQLAlchemyError:
            raise


    # ============================================================
    # Revenue Queries
    # ============================================================

    async def get_revenue_summary(
        self,
        owner_id: UUID,
    ):
        try:

            result = await self.db.execute(

                select(

                    func.count(Payment.id).label(
                        "total_payments",
                    ),

                    func.coalesce(
                        func.sum(Payment.amount),
                        0,
                    ).label(
                        "total_revenue",
                    ),

                    func.coalesce(
                        func.avg(Payment.amount),
                        0,
                    ).label(
                        "average_payment_amount",
                    ),

                )
                .join(
                    Booking,
                    Booking.id == Payment.booking_id,
                )
                .join(
                    Property,
                    Property.id == Booking.property_id,
                )
                .where(
                    Property.owner_id == owner_id,
                    Payment.payment_status == PaymentStatus.SUCCESS,
                )

            )

            (
                total_payments,
                total_revenue,
                average_payment_amount,
            ) = result.one()

            return {

                "total_payments": total_payments,

                "total_revenue": total_revenue,

                "average_payment_amount": average_payment_amount,

            }

        except SQLAlchemyError:
            raise

    # ============================================================
    # Booking History Commands
    # ============================================================

    async def create_booking_history(
        self,
        booking_history: BookingHistory,
    ) -> BookingHistory:
        """
        Create a booking history entry.
        """
        try:

            self.db.add(
                booking_history,
            )

            await self.db.flush()

            await self.db.refresh(
                booking_history,
            )

            return booking_history

        except SQLAlchemyError:

            await self.db.rollback()

            raise

    