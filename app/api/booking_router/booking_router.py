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

from app.dependencies.auth import (
    get_current_user,
    require_permission,
)

from app.models.users_models.users import User

from app.schema.booking_schema.booking_schemas import (
    BookingResponse,
    BookingSummaryResponse,
    CancelBookingRequest,
    CreateBookingRequest,
)

from app.services.booking_services.booking_service import (
    BookingService,
)

router = APIRouter(
    prefix="/bookings",
    tags=["Bookings"],
)

# ============================================================
# Service Dependency
# ============================================================

def get_booking_service(
    db: AsyncSession = Depends(get_db),
) -> BookingService:

    return BookingService(db)



# ============================================================
# Create Booking
# ============================================================
@router.post(
    "",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(
            require_permission(
                "booking.create",
            )
        )
    ],
)

async def create_booking(
    request: CreateBookingRequest,
    current_user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
):

    return await service.create_booking(
        request=request,
        current_user=current_user,
    )


# ============================================================
# Get Bookings
# ============================================================

@router.get(
    "/me",
    response_model=list[BookingSummaryResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(
            require_permission(
                "booking.view",
            )
        )
    ],
)
async def get_my_bookings(
    current_user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
):

    return await service.get_my_bookings(
        current_user=current_user,
    )


# ============================================================
# Get Upcoming and Completed Bookings
# ============================================================

@router.get(
    "/me/upcoming",
    response_model=list[BookingSummaryResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(
            require_permission(
                "booking.view",
            )
        )
    ],
)
async def get_upcoming_bookings(
    current_user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
):

    return await service.get_upcoming_bookings(
        current_user=current_user,
    )


# ============================================================
# Get Completed Bookings
# ============================================================

@router.get(
    "/me/completed",
    response_model=list[BookingSummaryResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(
            require_permission(
                "booking.view",
            )
        )
    ],
)
async def get_completed_bookings(
    current_user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
):

    return await service.get_completed_bookings(
        current_user=current_user,
    )


# ============================================================
# Get Booking Details
# ============================================================

@router.get(
    "/{booking_id}",
    response_model=BookingResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(
            require_permission(
                "booking.view",
            )
        )
    ],
)
async def get_booking(
    booking_id: UUID,
    current_user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
):

    return await service.get_booking(
        booking_id=booking_id,
        current_user=current_user,
    )



# ============================================================
# Cancel Booking Status
# ============================================================
@router.patch(
    "/{booking_id}/cancel",
    response_model=BookingResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(
            require_permission(
                "booking.cancel",
            )
        )
    ],
)
async def cancel_booking(
    booking_id: UUID,
    request: CancelBookingRequest,
    current_user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
):

    return await service.cancel_booking(
        booking_id=booking_id,
        request=request,
        current_user=current_user,
    )





# ============================================================
# Check-in, Check-out, and Complete Booking Status
# ============================================================
@router.patch(
    "/{booking_id}/check-in",
    response_model=BookingResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(
            require_permission(
                "booking.checkin",
            )
        )
    ],
)
async def check_in(
    booking_id: UUID,
    current_user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
):

    return await service.check_in(
        booking_id=booking_id,
        current_user=current_user,
    )


# ============================================================
# Check-out Booking Status
# ============================================================

@router.patch(
    "/{booking_id}/check-out",
    response_model=BookingResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(
            require_permission(
                "booking.checkout",
            )
        )
    ],
)
async def check_out(
    booking_id: UUID,
    current_user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
):

    return await service.check_out(
        booking_id=booking_id,
        current_user=current_user,
    )


# ============================================================
# Complete Booking Status
# ============================================================

@router.patch(
    "/{booking_id}/complete",
    response_model=BookingResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(
            require_permission(
                "booking.complete",
            )
        )
    ],
)
async def complete_booking(
    booking_id: UUID,
    current_user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
):

    return await service.complete_booking(
        booking_id=booking_id,
        current_user=current_user,
    )