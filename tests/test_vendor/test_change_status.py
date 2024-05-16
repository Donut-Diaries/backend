import pytest

from beanie import Document
from fastapi import status
from unittest import mock

from src.vendor.models import Vendor

from .conftest import API_PREFIX


@pytest.mark.asyncio
async def test_change_status_not_authenticated(client):
    response = await client.patch(f"{API_PREFIX}/change-status?new_status=Open")

    assert response is not None
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_change_status_authenticated(client_with_auth_vendor, vendor_in):
    # Add a vendor to the db
    await Vendor(**vendor_in).insert()

    # Vendor is closed
    vendor = await Vendor.get(vendor_in["id"])
    assert vendor.status == "Closed"

    # set status to open
    response = await client_with_auth_vendor.patch(
        f"{API_PREFIX}/change-status?new_status=Open"
    )

    assert response is not None
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"detail": "status updated", "status": "Open"}

    # set status to closed
    response1 = await client_with_auth_vendor.patch(
        f"{API_PREFIX}/change-status?new_status=Closed"
    )

    assert response1 is not None
    assert response1.status_code == status.HTTP_200_OK
    assert response1.json() == {"detail": "status updated", "status": "Closed"}


@pytest.mark.asyncio
async def test_change_status_vendor_missing(client_with_auth_vendor):
    # set status to open
    response = await client_with_auth_vendor.patch(
        f"{API_PREFIX}/change-status?new_status=Open"
    )

    assert response is not None
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Vendor not found"}


@pytest.mark.asyncio
async def test_change_status_server_error(client_with_auth_vendor, vendor_in):
    # Add a vendor to the db
    await Vendor(**vendor_in).insert()

    with mock.patch.object(Document, "save", side_effect=Exception()):

        # set status to open
        response = await client_with_auth_vendor.patch(
            f"{API_PREFIX}/change-status?new_status=Open"
        )

        assert response is not None
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json() == {"detail": "Unable to update status"}
