from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException

from src.auth.jwt_bearer import SupabaseJWTBearer, SupabaseJWTPayload
from src.vendor.models import Vendor, VendorCreate


def vendor_credentials(
    credentials: Annotated[SupabaseJWTPayload, Depends(SupabaseJWTBearer())]
):
    """Get dictionary representation of the SupabaseJWTPayload.

    Args:
        credentials (SupabaseJWTPayload): Credentials of the vendor.

    Returns:
        dict: Dictionary of the values in SupabaseJWTPayload
    """
    return credentials.model_dump()


async def get_vendor(
    credentials: dict = Depends(vendor_credentials),
) -> Vendor | None:
    """Get a vendor from the database.

    Args:
        credentials (dict, optional): Dictionary of the vendors details from the
            SupabaseJWTPayload.

    Returns:
        Vendor | None: A vendor from the database or None if not found.
    """
    return await Vendor.get(UUID(credentials["sub"]))


async def vendor_exists(
    vendor: Vendor = Depends(get_vendor),
) -> Vendor | None:
    """Validates that a vendor exists.

    Raises:
        HTTPException: If the vendor does not exist.

    Returns:
        Vendor | None: Vendor if they exist, else None.
    """

    if vendor:
        return vendor

    raise HTTPException(status_code=400, detail="Vendor not found")


async def vendor_not_exists(
    vendor: Vendor = Depends(get_vendor),
) -> None:
    """Validate that a vendor does not exist.

    Raises:
        HTTPException: If the vendor already exists.
    """

    if vendor:
        raise HTTPException(status_code=400, detail="Vendor already exists.")


async def parse_new_vendor_details(
    vendor_create: VendorCreate,
    vendor_credentials: dict = Depends(vendor_credentials),
    _=Depends(vendor_not_exists),
) -> VendorCreate:
    """
    Parses vendor details from the SupabaseJWTPayload and the VendorCreate
    form data into one object that can be used during vendor creation.

    The `id`, `email` and `phone` from the `SupabaseJWTPayload` are used
    over those in the VendorCreate. If the email in SupabaseJWTPayload is not
    valid, then the one in VendorCreate is used.

    Vendor must not exist for this function to run. If they exist,
    `HTTPException` is thrown with status `400`.

    Args:
        vendor_create (VendorCreate): Provided data of the new Vendor to create
        vendor_credentials (dict, optional): Credentials of the new vendor from
            the SupabaseJWTPayload.

    Returns:
        VendorCreate: Full details about the new vendor.
    """

    vendor_create.id = vendor_credentials["sub"]
    vendor_create.phone = vendor_credentials["phone"]

    try:
        vendor_create.email = vendor_credentials["email"]
    except Exception:
        pass

    return vendor_create


async def get_vendor_by_name(vendor_name: str) -> Vendor | None:
    """
    Gets the vendor from the database by their name.

    Args:
        vendor_name (str): Name of the vendor.

    Raises:
        HTTPException: If the vendor does not exist

    Returns:
        Vendor | None: The vendor if they are found else None.
    """

    vendor: Vendor = await Vendor.find_one(
        Vendor.name == vendor_name, fetch_links=True
    )

    if not vendor:
        raise HTTPException(
            status_code=404,
            detail="The vendor `{}` does not exist.".format(vendor_name),
        )

    return vendor
