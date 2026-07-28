# ============================================================
# Standard Library
# ============================================================

import asyncio

# ============================================================
# Third Party
# ============================================================

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# ============================================================
# Local Imports
# ============================================================

from app.core.password import hash_password
from app.database import AsyncSessionLocal

from app.common.enums.user_enums.user_status import (
    UserStatus,
)

from app.models.permissions_models.permissions import Permission
from app.models.permissions_models.roles import Role
from app.models.permissions_models.roles_permission import RolePermission
from app.models.users_models.users import User

# ============================================================
# Default Roles
# ============================================================

ROLES = [
    ("SUPER_ADMIN", "Platform Owner"),
    ("PROPERTY_OWNER", "Hotel Owner"),
    ("CUSTOMER", "Customer"),
]

# ============================================================
# Default Permissions
# ============================================================

PERMISSIONS = [

    # Property
    ("property.create", "property", "Create Property"),
    ("property.update", "property", "Update Property"),
    ("property.delete", "property", "Delete Property"),
    ("property.view", "property", "View Property"),
    ("property.approve", "property", "Approve Property"),
    ("property.reject", "property", "Reject Property"),

    # Room
    ("room.create", "room", "Create Room"),
    ("room.update", "room", "Update Room"),
    ("room.delete", "room", "Delete Room"),
    ("room.view", "room", "View Room"),

    # Booking
    ("booking.create", "booking", "Create Booking"),
    ("booking.view", "booking", "View Booking"),
    ("booking.cancel", "booking", "Cancel Booking"),
    ("booking.checkin", "booking", "Check-In Guest"),
    ("booking.checkout", "booking", "Check-Out Guest"),
    ("booking.complete", "booking", "Complete Booking"),

    # Payment
    ("payment.view", "payment", "View Payment"),
    ("payment.refund", "payment", "Refund Payment"),

    # Review
    ("review.create", "review", "Create Review"),
    ("review.delete", "review", "Delete Review"),

    # User
    ("user.create", "user", "Create User"),
    ("user.update", "user", "Update User"),
    ("user.delete", "user", "Delete User"),
    ("user.view", "user", "View User"),

    # Amenity
    ("amenity.create", "amenity", "Create Amenity"),
    ("amenity.view", "amenity", "View Amenity"),
    ("amenity.update", "amenity", "Update Amenity"),
    ("amenity.delete", "amenity", "Delete Amenity"),
]

# ============================================================
# Role Permission Mapping
# ============================================================

ROLE_PERMISSIONS = {

    "SUPER_ADMIN": None,

    "PROPERTY_OWNER": {

        "property.create",
        "property.update",
        "property.view",

        "room.create",
        "room.update",
        "room.delete",
        "room.view",

        "booking.view",
        "booking.checkin",
        "booking.checkout",
        "booking.complete",

        "payment.view",

        "review.create",

        "amenity.view",
    },

    "CUSTOMER": {

        "property.view",

        "room.view",

        "booking.create",
        "booking.view",
        "booking.cancel",

        "payment.view",

        "review.create",

        "amenity.view",
    },
}

# ============================================================
# Seed Database
# ============================================================

async def seed_database(
    db: AsyncSession,
) -> None:
    """
    Seed default Roles, Permissions,
    Role-Permission mappings,
    and the default Super Admin.

    Safe to execute multiple times.
    """

    try:

        # ====================================================
        # Existing Roles
        # ====================================================

        existing_roles = {
            role.name: role
            for role in (
                await db.execute(
                    select(Role)
                )
            ).scalars().all()
        }

        for name, description in ROLES:

            if name not in existing_roles:

                role = Role(
                    name=name,
                    description=description,
                    is_active=True,
                    created_by="SYSTEM",
                    updated_by="SYSTEM",
                )

                db.add(role)

                existing_roles[name] = role

        # ====================================================
        # Existing Permissions
        # ====================================================

        existing_permissions = {
            permission.name: permission
            for permission in (
                await db.execute(
                    select(Permission)
                )
            ).scalars().all()
        }

        for name, module, description in PERMISSIONS:

            permission = existing_permissions.get(name)

            if permission is None:

                permission = Permission(
                    name=name,
                    module=module,
                    description=description,
                    created_by="SYSTEM",
                    updated_by="SYSTEM",
                )

                db.add(permission)

                existing_permissions[name] = permission

            else:

                permission.module = module
                permission.description = description
                permission.updated_by = "SYSTEM"

        # ====================================================
        # Flush IDs
        # ====================================================

        await db.flush()

        # ====================================================
        # Default Super Admin
        # ====================================================

        result = await db.execute(
            select(User).where(
                User.email == "admin@example.com",
            )
        )

        admin = result.scalar_one_or_none()

        if admin is None:

            admin = User(
                first_name="Super",
                last_name="Admin",
                email="admin@example.com",
                password_hash=hash_password(
                    "Admin@123",
                ),
                phone="9999999999",
                role_id=existing_roles["SUPER_ADMIN"].id,
                user_status=UserStatus.ACTIVE,
                created_by="SYSTEM",
                updated_by="SYSTEM",
            )

            db.add(admin)

        # ====================================================
        # Existing Role Permission Links
        # ====================================================

        existing_links = {

            (
                link.role_id,
                link.permission_id,
            )

            for link in (
                await db.execute(
                    select(RolePermission)
                )
            ).scalars().all()
        }

        for role_name, permission_names in ROLE_PERMISSIONS.items():

            role = existing_roles[role_name]

            if permission_names is None:
                permission_names = existing_permissions.keys()

            for permission_name in permission_names:

                permission = existing_permissions[
                    permission_name
                ]

                key = (
                    role.id,
                    permission.id,
                )

                if key in existing_links:
                    continue

                db.add(

                    RolePermission(
                        role_id=role.id,
                        permission_id=permission.id,
                        created_by="SYSTEM",
                        updated_by="SYSTEM",
                    )

                )

                existing_links.add(key)

        await db.commit()

        print("✓ Roles seeded successfully")
        print("✓ Permissions seeded successfully")
        print("✓ Super Admin created successfully")
        print("✓ Role-Permission mappings seeded successfully")

    except Exception:

        await db.rollback()

        raise


# ============================================================
# Run Seeder
# ============================================================

async def main() -> None:

    async with AsyncSessionLocal() as db:

        await seed_database(db)

        print("Database seeded successfully!")


if __name__ == "__main__":
    asyncio.run(main())