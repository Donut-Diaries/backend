import pytest
from copy import deepcopy
from fastapi import status
from uuid import UUID

from src.vendor.models import Vendor

from .conftest import API_PREFIX, VENDOR_DETAILS


@pytest.mark.asyncio
async def test_create_new_vendor_not_authenticated(client, vendor_out):
    response = await client.post(f"{API_PREFIX}/new", json=VENDOR_DETAILS)

    assert response is not None
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Not authenticated"}

    created_vendor = await Vendor.get(vendor_out["id"])

    assert created_vendor is None


@pytest.mark.asyncio
async def test_create_new_vendor_authenticated(
    client_with_auth_vendor, vendor_out
):
    # Does not exist in db
    vendor = await Vendor.get(vendor_out["id"])
    assert vendor is None

    # Create vendor
    response = await client_with_auth_vendor.post(
        f"{API_PREFIX}/new", json=VENDOR_DETAILS
    )

    assert response is not None
    assert response.status_code == status.HTTP_201_CREATED

    _vendor_out = deepcopy(vendor_out)
    del _vendor_out["queue"]

    vendor_details_copy = deepcopy(VENDOR_DETAILS)

    _vendor_out["menu"] = vendor_details_copy["menu"]
    del _vendor_out["menu"][0]["id"]

    r = response.json()

    assert UUID(r["queue"]["id"])
    del r["queue"]

    assert UUID(r["menu"][0]["id"])  # Ensure id is UUID
    del r["menu"][0]["id"]

    assert r == _vendor_out

    # Added to db
    created_vendor = await Vendor.get(vendor_out["id"])
    assert created_vendor is not None


@pytest.mark.asyncio
async def test_create_duplicate_vendor(client_with_auth_vendor, vendor_in):
    # Insert new vendor
    await Vendor(**vendor_in).insert()

    created_vendor = await Vendor.get(vendor_in["id"])

    assert created_vendor is not None

    # Insert duplicate vendor
    response = await client_with_auth_vendor.post(
        f"{API_PREFIX}/new", json=VENDOR_DETAILS
    )

    assert response is not None
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Vendor already exists."}


@pytest.mark.asyncio
async def test_create_new_vendor_invalid_name(
    client_with_auth_vendor, vendor_out
):
    invalid_vendor_details = deepcopy(VENDOR_DETAILS)
    invalid_vendor_details["name"] = ""

    response = await client_with_auth_vendor.post(
        f"{API_PREFIX}/new", json=invalid_vendor_details
    )

    assert response is not None
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "type": "value_error",
                "loc": ["body"],
                "msg": "Value error, Cannot provide empty vendor name",
                "input": invalid_vendor_details,
                "ctx": {"error": {}},
                "url": "https://errors.pydantic.dev/2.6/v/value_error",
            }
        ]
    }

    created_vendor = await Vendor.get(vendor_out["id"])

    assert created_vendor is None


@pytest.mark.asyncio
async def test_create_new_vendor_invalid_email(
    client_with_auth_vendor, vendor_out
):
    invalid_vendor_details = VENDOR_DETAILS.copy()
    invalid_vendor_details["email"] = ""

    response = await client_with_auth_vendor.post(
        f"{API_PREFIX}/new", json=invalid_vendor_details
    )

    assert response is not None
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "type": "value_error",
                "loc": ["body", "email"],
                "msg": "value is not a valid email address: The email address is not valid. It must have exactly one @-sign.",
                "input": "",
                "ctx": {
                    "reason": "The email address is not valid. It must have exactly one @-sign."
                },
            }
        ]
    }

    created_vendor = await Vendor.get(vendor_out["id"])

    assert created_vendor is None
