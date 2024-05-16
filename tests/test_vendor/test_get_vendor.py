import pytest

from beanie import WriteRules
from fastapi import status

from src.vendor.models import Vendor

from .conftest import API_PREFIX


@pytest.mark.asyncio
async def test_get_vendor_not_authenticated(client):
    response = await client.get(f"{API_PREFIX}")

    assert response is not None
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_vendor_authenticated(
    client_with_auth_vendor,
    vendor_in,
    vendor_out,
):
    # Add a vendor to the db
    await Vendor(**vendor_in).insert(link_rule=WriteRules.WRITE)

    response = await client_with_auth_vendor.get(f"{API_PREFIX}")

    assert response is not None
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == vendor_out


@pytest.mark.asyncio
async def test_get_vendor_authenticated_not_added(client_with_auth_vendor):
    # Authenticated vendor not created in db

    response = await client_with_auth_vendor.get(f"{API_PREFIX}")

    assert response is not None
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Vendor not found"}


@pytest.mark.asyncio
async def test_get_vendor_by_name_not_authenticated(
    client,
    vendor_in,
    vendor_out,
):
    # Add a vendor to the db
    await Vendor(**vendor_in).insert(link_rule=WriteRules.WRITE)

    response = await client.get(f"{API_PREFIX}/{vendor_in["name"]}")

    assert response is not None
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == vendor_out


@pytest.mark.asyncio
async def test_get_vendor_by_name_authenticated(
    client_with_auth_vendor,
    vendor_in,
    vendor_out,
):
    # Add a vendor to the db
    await Vendor(**vendor_in).insert(link_rule=WriteRules.WRITE)

    response = await client_with_auth_vendor.get(
        f"{API_PREFIX}/{vendor_in["name"]}"
    )

    assert response is not None
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == vendor_out


@pytest.mark.asyncio
async def test_get_vendor_by_name_vendor_missing(client):
    # No vendor has been added

    response = await client.get(f"{API_PREFIX}/invalid-vendor-name")

    assert response is not None
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "The vendor `invalid-vendor-name` does not exist."
    }
