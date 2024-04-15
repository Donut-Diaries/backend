from fastapi import APIRouter, Depends, status

from src.auth.jwt_bearer import SupabaseJWTBearer
from src.vendor.dependencies import (
    get_vendor_by_name,
    vendor_exists,
    parse_new_vendor_details,
)
from src.vendor.models import Vendor, VendorCreate, VendorOut, FoodOut
from src.vendor.service import create_vendor
from src.vendor.schema import HTTPError


router = APIRouter(
    prefix="/vendor",
    tags=["vendor"],
    dependencies=[Depends(SupabaseJWTBearer)],
)


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=VendorOut,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": HTTPError,
            "description": "Vendor does not exist",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": HTTPError,
            "description": "Forbidden",
        },
    },
)
async def get_vendor(vendor: Vendor = Depends(vendor_exists)) -> VendorOut:
    return vendor


@router.post(
    "/new",
    status_code=status.HTTP_201_CREATED,
    response_model=VendorOut,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": HTTPError,
            "description": "Vendor already exists",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": HTTPError,
            "description": "Forbidden",
        },
    },
)
async def new_vendor(
    vendor_details: VendorCreate = Depends(parse_new_vendor_details),
) -> VendorOut:

    vendor = await create_vendor(vendor_details=vendor_details)

    return vendor


@router.get(
    "/{vendor_name}/menu",
    status_code=status.HTTP_200_OK,
    response_model=list[FoodOut],
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": HTTPError,
            "description": "Vendor not found",
        }
    },
)
async def menu(vendor: Vendor = Depends(get_vendor_by_name)) -> list[FoodOut]:
    """Gets the list of the foods that a vendor provides"""
    return vendor.menu
