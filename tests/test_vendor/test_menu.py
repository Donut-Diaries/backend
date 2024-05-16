import pytest

from beanie import WriteRules
from fastapi import status

from src.main import app
from src.vendor.dependencies import get_vendor_menu
from src.vendor.models import Food, Vendor

from .conftest import API_PREFIX, VENDOR_DETAILS


@pytest.mark.asyncio
async def test_get_vendor_menu_vendor_missing(client):
    response = await client.get(
        f"{API_PREFIX}/{VENDOR_DETAILS["name"]}/menu"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "The vendor `Test vendor` does not exist."
    }


@pytest.mark.asyncio
async def test_get_vendor_menu_ok(client, vendor_in, fastapi_dep, food_out):

    # Add a vendor to the db
    await Vendor(**vendor_in).insert(link_rule=WriteRules.WRITE)

    vendor = await Vendor.get(vendor_in["id"])

    await vendor.fetch_link("menu")

    with fastapi_dep(app).override({get_vendor_menu: lambda: vendor.menu}):
        response = await client.get(
            f"{API_PREFIX}/{VENDOR_DETAILS["name"]}/menu"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == [food_out]


@pytest.mark.asyncio
async def test_get_food_vendor_missing(client):
    response = await client.get(
        f"{API_PREFIX}/{VENDOR_DETAILS["name"]}/menu/food-name"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "The vendor `Test vendor` does not exist."
    }


@pytest.mark.asyncio
async def test_get_food_not_found(client, vendor_in):
    # Add a vendor to the db
    await Vendor(**vendor_in).insert(link_rule=WriteRules.WRITE)

    response = await client.get(
        f"{API_PREFIX}/{VENDOR_DETAILS["name"]}/menu/food-name"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "The food `food-name` not found."}


@pytest.mark.asyncio
async def test_get_food_ok(client, vendor_in, food_out):
    # Add a vendor to the db
    await Vendor(**vendor_in).insert(link_rule=WriteRules.WRITE)

    response = await client.get(
        f"{API_PREFIX}/{vendor_in["name"]}/menu/{vendor_in["menu"][0]["name"]}"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == food_out


@pytest.mark.asyncio
async def test_add_food_to_menu_ok(client_with_auth_vendor, vendor_in):
    # Add a vendor to the db
    await Vendor(**vendor_in).insert(link_rule=WriteRules.WRITE)

    new_food = {
        "id": "6cd4a106-1200-11ef-8495-e86a64c3b96f",
        "name": "Test food 1",
        "available": False,
        "ttp": 1,
        "description": "Test adding using /api/vendor/menu",
        "picture": ["url to test food pic"],
        "ingredients": [],
        "category": [
            "test",
        ],
        "price": {
            "amount": 100.0,
            "currency": "Ksh",
        },
    }

    response = await client_with_auth_vendor.post(
        f"{API_PREFIX}/menu", json=new_food
    )

    new_food_out = new_food.copy()
    del new_food_out["id"]

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == [new_food_out]

    vendor = await Vendor.get(vendor_in["id"])

    await vendor.fetch_link("menu")

    assert vendor is not None
    assert len(vendor.menu) == 2
    assert new_food["name"] in [
        food.model_dump()["name"] for food in vendor.menu
    ]


@pytest.mark.asyncio
async def test_add_food_to_menu_not_authenticated(client):
    response = await client.post(f"{API_PREFIX}/menu")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_add_food_to_menu_vendor_missing(client_with_auth_vendor):
    # Vendor not added to db

    new_food = {
        "id": "6cd4a106-1200-11ef-8495-e86a64c3b96f",
        "name": "Test food 1",
        "available": False,
        "ttp": 1,
        "description": "Test adding using /api/vendor/menu",
        "picture": ["url to test food pic"],
        "ingredients": [],
        "category": [
            "test",
        ],
        "price": {
            "amount": 100.0,
            "currency": "Ksh",
        },
    }

    response = await client_with_auth_vendor.post(
        f"{API_PREFIX}/menu", json=new_food
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Vendor not found"}


@pytest.mark.asyncio
async def test_add_food_to_menu_validation_error(
    client_with_auth_vendor, vendor_in
):
    # Add a vendor to the db
    await Vendor(**vendor_in).insert(link_rule=WriteRules.WRITE)

    # Invalid food missing name
    invalid_food = {
        "id": "6cd4a106-1200-11ef-8495-e86a64c3b96f",
        "available": False,
        "ttp": 1,
        "description": "Test adding using /api/vendor/menu",
        "picture": ["url to test food pic"],
        "ingredients": [],
        "category": [
            "test",
        ],
        "price": {
            "amount": 100.0,
            "currency": "Ksh",
        },
    }

    response = await client_with_auth_vendor.post(
        f"{API_PREFIX}/menu", json=invalid_food
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_update_food_in_menu_ok(
    client_with_auth_vendor, vendor_in, food_out
):
    # Add a vendor to the db
    await Vendor(**vendor_in).insert(link_rule=WriteRules.WRITE)

    # Food values to update
    food_update = {
        "name": "Updated food",
        "description": "Update a food in the menu",
    }

    response = await client_with_auth_vendor.patch(
        f"{API_PREFIX}/menu?food_id={vendor_in["menu"][0]["id"]}",
        json=food_update,
    )

    updated_food_out = food_out.copy()
    updated_food_out["name"] = food_update["name"]
    updated_food_out["description"] = food_update["description"]

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == updated_food_out

    # Check the food in db is updated
    food = await Food.get(vendor_in["menu"][0]["id"])

    assert food is not None
    assert food.model_dump()["name"] == food_update["name"]
    assert food.model_dump()["description"] == food_update["description"]


@pytest.mark.asyncio
async def test_update_food_in_menu_empty_food_update(
    client_with_auth_vendor, vendor_in, food_out
):
    # Add a vendor to the db
    await Vendor(**vendor_in).insert(link_rule=WriteRules.WRITE)

    response = await client_with_auth_vendor.patch(
        f"{API_PREFIX}/menu?food_id={vendor_in["menu"][0]["id"]}",
        json={},
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == food_out  # Food remains the same

    # Check the food in db is same
    food = await Food.get(vendor_in["menu"][0]["id"])

    assert food is not None
    assert food.model_dump()["name"] == vendor_in["menu"][0]["name"]
    assert (
        food.model_dump()["description"] == vendor_in["menu"][0]["description"]
    )


@pytest.mark.asyncio
async def test_update_food_in_menu_not_authenticated(client, vendor_in):

    response = await client.patch(
        f"{API_PREFIX}/menu?food_id={vendor_in["menu"][0]["id"]}",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_update_food_in_menu_vendor_not_found(
    client_with_auth_vendor, food_in
):
    # Ensure the food is inserted
    await Food(**food_in).insert()

    response = await client_with_auth_vendor.patch(
        f"{API_PREFIX}/menu?food_id={food_in["id"]}",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Vendor not found"}


@pytest.mark.asyncio
async def test_update_food_in_menu_food_not_found(
    client_with_auth_vendor, vendor_in, food_in
):

    # Add a vendor to the db without inserting food
    await Vendor(**vendor_in).insert()

    response = await client_with_auth_vendor.patch(
        f"{API_PREFIX}/menu?food_id={food_in["id"]}",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Invalid food id"}


@pytest.mark.asyncio
async def test_delete_food_from_menu_ok(client_with_auth_vendor, vendor_in):
    # Add a vendor to the db
    await Vendor(**vendor_in).insert(link_rule=WriteRules.WRITE)

    vendor = await Vendor.get(vendor_in["id"])

    assert vendor is not None
    assert len(vendor.menu) == 1

    response = await client_with_auth_vendor.delete(
        f"{API_PREFIX}/menu?food_id={vendor_in["menu"][0]["id"]}",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"detail": "OK"}

    await vendor.sync()  # Sync with db

    assert len(vendor.menu) == 0


@pytest.mark.asyncio
async def test_delete_food_from_menu_not_authenticated(client, vendor_in):
    response = await client.delete(
        f"{API_PREFIX}/menu?food_id={vendor_in["menu"][0]["id"]}",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_delete_food_from_menu_vendor_not_found(
    client_with_auth_vendor, food_in
):
    await Food(**food_in).insert()

    response = await client_with_auth_vendor.delete(
        f"{API_PREFIX}/menu?food_id={food_in["id"]}",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Vendor not found"}


@pytest.mark.asyncio
async def test_delete_food_from_menu_food_not_found(
    client_with_auth_vendor, vendor_in
):

    # Add a vendor to the db without inserting food
    await Vendor(**vendor_in).insert()

    response = await client_with_auth_vendor.delete(
        f"{API_PREFIX}/menu?food_id={vendor_in["menu"][0]["id"]}",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Invalid food id"}
