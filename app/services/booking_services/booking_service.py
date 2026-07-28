# ============================================================
# Standard Library
# ============================================================
from __future__ import annotations
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

# ============================================================
# Third Party
# ============================================================

from fastapi import (
    HTTPException,
    status,
)

from sqlalchemy.ext.asyncio import AsyncSession

# ============================================================
# Local Imports
# ============================================================

from app.common.enums.booking_enums.booking_enums import (
    BookingStatus,
    CancellationType,
    PaymentStatus,
    RefundStatus,
)

from app.common.enums.property_enums.property_status import (
    PropertyStatus,
)

from app.common.enums.room_enums.room_status import (
    RoomStatus,
)

from app.common.enums.user_enums.role_name import (
    RoleName,
)

from app.models.booking_models import booking
from app.models.booking_models.booking import (
    Booking,
)

from app.models.booking_models.booking_cancellation import (
    BookingCancellation,
)

from app.models.booking_models.booking_history import (
    BookingHistory,
)

from app.models.booking_models.booking_room import (
    BookingRoom,
)

from app.repositories.booking_repositories.booking_repository import (
    BookingRepository,
)

from app.schema.booking_schema.booking_schemas import (
    BookingResponse,
    BookingRoomResponse,
    BookingSummaryResponse,
    CancelBookingRequest,
    CreateBookingRequest,
)

if TYPE_CHECKING:
    from app.models.users_models.users import User
    
# ============================================================
# Booking Service
# ============================================================

class BookingService:

    def __init__(
        self,
        db: AsyncSession,
    ):
        self.db = db
        self.repo = BookingRepository(db)

    # ========================================================
    # Validate Property
    # ========================================================

    async def _validate_property(
        self,
        property_id: UUID,
    ):

        property_obj = await self.repo.get_property_by_id(
            property_id,
        )

        if property_obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found.",
            )

        if property_obj.status != PropertyStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Property is not available for booking.",
            )

        return property_obj

    # ========================================================
    # Validate Stay Dates
    # ========================================================

    def _validate_booking_dates(
        self,
        check_in: date,
        check_out: date,
    ):

        today = date.today()

        if check_in < today:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Check-in date cannot be in the past.",
            )

        if check_out <= check_in:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Check-out date must be after check-in date.",
            )

    # ========================================================
    # Generate Booking Reference
    # ========================================================

    def _generate_booking_reference(
        self,
    ) -> str:

        return f"BK-{uuid4().hex[:10].upper()}"

    # ========================================================
    # Validate Selected Rooms
    # ========================================================

    async def _validate_rooms(
        self,
        request: CreateBookingRequest,
    ):

        room_ids = [
            room.room_id
            for room in request.rooms
        ]

        if len(room_ids) != len(set(room_ids)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate rooms are not allowed in a booking.",
            )
        rooms = await self.repo.get_rooms_by_ids(
            room_ids,
        )
        if not rooms:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No rooms found.",
            )
        
        if len(rooms) != len(room_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more rooms do not exist.",
            )

        for room in rooms:

            if room.room_type.property_id != request.property_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Selected room does not belong to the selected property.",
                )

            if not room.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Room {room.room_number} is inactive.",
                )

            if room.status != RoomStatus.AVAILABLE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Room {room.room_number} is not available.",
                )

            available = await self.repo.check_room_availability(
                room.id,
                request.check_in_date,
                request.check_out_date,
            )

            if not available:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Room {room.room_number} is already booked.",
                )

        return rooms

    # ========================================================
    # Validate Guest Capacity
    # ========================================================

    def _validate_guest_capacity(
        self,
        rooms: list,
        adult_count: int,
        child_count: int,
    ) -> None:

        total_adults = sum(
            room.room_type.max_adults
            for room in rooms
        )

        total_children = sum(
            room.room_type.max_children
            for room in rooms
        )

        if adult_count > total_adults:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected rooms cannot accommodate all adults.",
            )

        if child_count > total_children:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected rooms cannot accommodate all children.",
            )

    # ========================================================
    # Calculate Pricing
    # ========================================================

    def _calculate_pricing(
        self,
        rooms: list,
        check_in: date,
        check_out: date,
    ):

        nights = (
            check_out - check_in
        ).days

        subtotal = Decimal("0.00")

        booking_rooms = []

        for room in rooms:

            price = room.room_type.base_price

            room_total = (
                price * nights
            )

            subtotal += room_total

            booking_rooms.append(

                BookingRoom(
                    room_id=room.id,
                    price_per_night=price,
                    number_of_nights=nights,
                    room_total=room_total,
                )
            )

        tax_amount = Decimal("0.00")

        discount_amount = Decimal("0.00")

        total_amount = (
            subtotal
            + tax_amount
            - discount_amount
        )

        return (
            booking_rooms,
            subtotal,
            tax_amount,
            discount_amount,
            total_amount,
        )

    # ========================================================
    # Build Booking Response
    # ========================================================

    def _build_booking_response(
        self,
        booking: Booking,
    ) -> BookingResponse:

        return BookingResponse(
            id=booking.id,
            booking_reference=booking.booking_reference,
            customer_id=booking.customer_id,
            property_id=booking.property_id,
            check_in_date=booking.check_in_date,
            check_out_date=booking.check_out_date,
            adult_count=booking.adult_count,
            child_count=booking.child_count,
            subtotal=booking.subtotal,
            tax_amount=booking.tax_amount,
            discount_amount=booking.discount_amount,
            total_amount=booking.total_amount,
            booking_status=booking.booking_status,
            payment_status=booking.payment_status,
            special_requests=booking.special_requests,
            rooms=[
                BookingRoomResponse(
                    room_id=item.room.id,
                    room_number=item.room.room_number,
                    room_type=item.room.room_type.room_name,
                    price_per_night=item.price_per_night,
                    number_of_nights=item.number_of_nights,
                    room_total=item.room_total,
                )
                for item in booking.booking_rooms
            ],
        )


    # ========================================================
    # Create Booking
    # ========================================================

    async def create_booking(
        self,
        request: CreateBookingRequest,
        current_user: User,
    ) -> Booking:

        try: 
            # ----------------------------------------------------
            # Validate Property
            # ----------------------------------------------------

            await self._validate_property(
                request.property_id,
            )

            # ----------------------------------------------------
            # Validate Stay Dates
            # ----------------------------------------------------

            self._validate_booking_dates(
                request.check_in_date,
                request.check_out_date,
            )

            # ----------------------------------------------------
            # Validate Rooms
            # ----------------------------------------------------

            rooms = await self._validate_rooms(
                request,
            )

            # ----------------------------------------------------
            # Validate Guest Capacity
            # ----------------------------------------------------

            self._validate_guest_capacity(
                rooms=rooms,
                adult_count=request.adult_count,
                child_count=request.child_count,
            )

            # ----------------------------------------------------
            # Calculate Pricing
            # ----------------------------------------------------

            (
                booking_rooms,
                subtotal,
                tax_amount,
                discount_amount,
                total_amount,
            ) = self._calculate_pricing(
                rooms=rooms,
                check_in=request.check_in_date,
                check_out=request.check_out_date,
            )

            # ----------------------------------------------------
            # Create Booking
            # ----------------------------------------------------

            booking = Booking(

                customer_id=current_user.id,

                property_id=request.property_id,

                booking_reference=self._generate_booking_reference(),

                check_in_date=request.check_in_date,

                check_out_date=request.check_out_date,

                adult_count=request.adult_count,

                child_count=request.child_count,

                subtotal=subtotal,

                tax_amount=tax_amount,

                discount_amount=discount_amount,

                total_amount=total_amount,

                booking_status=BookingStatus.PENDING,

                payment_status=PaymentStatus.PENDING,

                special_requests=request.special_requests,

                created_by=current_user.email,

                updated_by=current_user.email,
            )

            booking = await self.repo.create_booking(
                booking,
            )

            # ----------------------------------------------------
            # Attach Booking ID to Booking Rooms
            # ----------------------------------------------------

            for room in booking_rooms:

                room.booking_id = booking.id

            await self.repo.create_booking_rooms(
                booking_rooms,
            )

            # ----------------------------------------------------
            # Create Initial Booking History
            # ----------------------------------------------------

            history = BookingHistory(

                booking_id=booking.id,

                old_status=BookingStatus.PENDING,

                new_status=BookingStatus.PENDING,

                changed_by=current_user.id,

                remarks="Booking created.",

                created_by=current_user.email,

                updated_by=current_user.email,
            )

            await self.repo.create_booking_history(
                history,
            )

            # ----------------------------------------------------
            # Commit Transaction
            # ----------------------------------------------------

            await self.db.commit()

            # ----------------------------------------------------
            # Return Complete Booking
            # ----------------------------------------------------

            booking = await self.repo.get_booking_details(
                booking.id,
            )

            return self._build_booking_response(
                booking,
            )

        except Exception:

            await self.db.rollback()

            raise
    # ========================================================
    # Get Booking By ID
    # ========================================================

    async def get_booking(
        self,
        booking_id: UUID,
        current_user: User,
    ) -> Booking:

        booking = await self._get_booking_or_404(
            booking_id,
        )

        await self._validate_booking_access(
            booking,
            current_user,
        )

        booking = await self.repo.get_booking_details(
            booking.id,
        )

        return self._build_booking_response(
            booking,
        )

    # ========================================================
    # Get My Bookings
    # ========================================================

    async def get_my_bookings(
        self,
        current_user: User,
    ) -> list[Booking]:

        return await self.repo.get_customer_bookings(
            customer_id=current_user.id,
        )

    # ========================================================
    # Get Upcoming Bookings
    # ========================================================

    async def get_upcoming_bookings(
        self,
        current_user: User,
    ) -> list[Booking]:

        return await self.repo.get_upcoming_bookings(
            customer_id=current_user.id,
            today=date.today(),
        )

    # ========================================================
    # Get Completed Bookings
    # ========================================================

    async def get_completed_bookings(
        self,
        current_user: User,
    ) -> list[Booking]:

        return await self.repo.get_completed_bookings(
            customer_id=current_user.id,
        )

    # ========================================================
    # Get Booking Or 404
    # ========================================================

    async def _get_booking_or_404(
        self,
        booking_id: UUID,
    ) -> Booking:

        booking = await self.repo.get_booking_details(
            booking_id,
        )

        if booking is None:

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found.",
            )

        return booking

    # ========================================================
    # Validate Booking Access
    # ========================================================

    async def _validate_booking_access(
        self,
        booking: Booking,
        current_user: User,
    ) -> None:

        if current_user.role.name == RoleName.SUPER_ADMIN.value:
            return

        if current_user.role.name == RoleName.CUSTOMER.value:

            if booking.customer_id != current_user.id:

                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not allowed to access this booking.",
                )

            return

        if current_user.role.name == RoleName.PROPERTY_OWNER.value:

            property_obj = await self.repo.get_property_by_id(
                booking.property_id,
            )

            if property_obj is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Property not found.",
                )

            if property_obj.owner_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not allowed to access this booking.",
                )

            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )

        # ========================================================
    # Cancel Booking
    # ========================================================

    async def cancel_booking(
        self,
        booking_id: UUID,
        request: CancelBookingRequest,
        current_user: User,
    ) -> Booking:

        try:
            booking = await self._get_booking_or_404(
                booking_id,
            )

            await self._validate_booking_access(
                booking,
                current_user,
            )

            if booking.booking_status in (
                BookingStatus.CHECKED_IN,
                BookingStatus.CHECKED_OUT,
                BookingStatus.COMPLETED,
                BookingStatus.CANCELLED,
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This booking cannot be cancelled.",
                )

            cancellation = BookingCancellation(
                booking_id=booking.id,
                cancellation_type=self._get_cancellation_type(
                    current_user,
                ),
                reason=request.reason,
                refund_status=RefundStatus.PENDING,
                refund_amount=Decimal("0.00"),
                cancelled_by=current_user.id,
                created_by=current_user.email,
                updated_by=current_user.email,
            )

            await self.repo.create_booking_cancellation(
                cancellation,
            )

            old_status = booking.booking_status

            booking.booking_status = BookingStatus.CANCELLED
            booking.updated_by = current_user.email

            await self._create_booking_history(
                booking=booking,
                old_status=old_status,
                new_status=BookingStatus.CANCELLED,
                changed_by=current_user,
                remarks="Booking cancelled.",
            )

            await self.db.commit()

            booking = await self.repo.get_booking_details(
                booking.id,
            )

            return self._build_booking_response(
                booking,
            )
        
        except Exception:
            await self.db.rollback()
            raise
    
    # ========================================================
    # Check In
    # ========================================================

    async def check_in(
        self,
        booking_id: UUID,
        current_user: User,
    ) -> Booking:
        try:
            booking = await self._get_booking_or_404(
                booking_id,
            )

            await self._validate_owner_access(
                booking,
                current_user,
            )

            today = date.today()

            if today < booking.check_in_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Guest cannot check in before the booking date.",
                )
            
            if booking.booking_status != BookingStatus.CONFIRMED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Booking is not ready for check-in.",
                )

            old_status = booking.booking_status

            booking.booking_status = BookingStatus.CHECKED_IN
            booking.updated_by = current_user.email

            await self._create_booking_history(
                booking=booking,
                old_status=old_status,
                new_status=BookingStatus.CHECKED_IN,
                changed_by=current_user,
                remarks="Guest checked in.",
            )

            await self.db.commit()

            booking = await self.repo.get_booking_details(
                booking.id,
            )

            return self._build_booking_response(
                booking,
            )
        except Exception:
            await self.db.rollback()
            raise
    

    # ========================================================
    # Check Out
    # ========================================================

    async def check_out(
        self,
        booking_id: UUID,
        current_user: User,
    ) -> Booking:

        try:
            booking = await self._get_booking_or_404(
                booking_id,
            )

            await self._validate_owner_access(
                booking,
                current_user,
            )

            today = date.today()

            if today < booking.check_out_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Guest cannot check out before the scheduled check-out date.",
                )

            if booking.booking_status != BookingStatus.CHECKED_IN:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Booking is not checked in.",
                )

            old_status = booking.booking_status

            booking.booking_status = BookingStatus.CHECKED_OUT
            booking.updated_by = current_user.email

            await self._create_booking_history(
                booking=booking,
                old_status=old_status,
                new_status=BookingStatus.CHECKED_OUT,
                changed_by=current_user,
                remarks="Guest checked out.",
            )

            await self.db.commit()

            booking = await self.repo.get_booking_details(
                booking.id,
            )

            return self._build_booking_response(
                booking,
            )
        except Exception:
            await self.db.rollback()
            raise
   

    # ========================================================
    # Complete Booking
    # ========================================================

    async def complete_booking(
        self,
        booking_id: UUID,
        current_user: User,
    ) -> Booking:
        try:
            booking = await self._get_booking_or_404(
                booking_id,
            )

            await self._validate_owner_access(
                booking,
                current_user,
            )

            if booking.booking_status != BookingStatus.CHECKED_OUT:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Booking must be checked out first.",
                )

            old_status = booking.booking_status

            booking.booking_status = BookingStatus.COMPLETED
            booking.updated_by = current_user.email

            await self._create_booking_history(
                booking=booking,
                old_status=old_status,
                new_status=BookingStatus.COMPLETED,
                changed_by=current_user,
                remarks="Booking completed.",
            )

            await self.db.commit()

            booking = await self.repo.get_booking_details(
                booking.id,
            )

            return self._build_booking_response(
                booking,
            )
        except Exception:
            await self.db.rollback()
            raise
    # ========================================================
    # Create Booking History
    # ========================================================

    async def _create_booking_history(
        self,
        booking: Booking,
        old_status: BookingStatus,
        new_status: BookingStatus,
        changed_by: User,
        remarks: str,
    ) -> None:

        history = BookingHistory(
            booking_id=booking.id,
            old_status=old_status,
            new_status=new_status,
            changed_by=changed_by.id,
            remarks=remarks,
            created_by=changed_by.email,
            updated_by=changed_by.email,
        )

        await self.repo.create_booking_history(
            history,
        )
    # ========================================================
    # Get Cancellation Type
    # ========================================================

    def _get_cancellation_type(
        self,
        current_user: User,
    ) -> CancellationType:

        if current_user.role.name == RoleName.CUSTOMER.value:
            return CancellationType.CUSTOMER

        if current_user.role.name == RoleName.PROPERTY_OWNER.value:
            return CancellationType.PROPERTY_OWNER

        if current_user.role.name == RoleName.SUPER_ADMIN.value:
            return CancellationType.SUPER_ADMIN

        return CancellationType.SYSTEM

    # ========================================================
    # Validate Owner Access
    # ========================================================

    async def _validate_owner_access(
        self,
        booking: Booking,
        current_user: User,
    ) -> None:

        if current_user.role.name == RoleName.SUPER_ADMIN.value:
            return

        if current_user.role.name != RoleName.PROPERTY_OWNER.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied.",
            )

        property_obj = await self.repo.get_property_by_id(
            booking.property_id,
        )

        if property_obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found.",
            )

        if property_obj.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to manage this booking.",
            )