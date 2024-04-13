from fastapi import APIRouter, Depends, status

from src.auth.jwt_bearer import SupabaseJWTBearer
from src.vendor.dependencies import (
    vendor_exists,
    parse_new_vendor_details,
)
from src.vendor.models import Vendor, VendorCreate, VendorOut
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
    response_model_exclude="_id",
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
