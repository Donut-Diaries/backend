import pytest
import pytest_asyncio
import unittest.mock as mock

from asgi_lifespan import LifespanManager
from httpx import AsyncClient
from uuid import UUID
from bson.binary import Binary, UuidRepresentation, UUID_SUBTYPE

from src.main import app
from src.vendor.dependencies import vendor_credentials

API_PREFIX = "/api/vendor"


FOOD_DETAILS = {
    "id": "6cd4a106-1200-11ef-8495-e86a64c3b96e",
    "name": "Test food",
    "available": True,
    "ttp": 10,
    "description": "This is a test food",
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


VENDOR_DETAILS = {
    "name": "Test vendor",
    "description": "Vendor for testing",
    "status": "Closed",
    "location": {"street": "Q avenue", "town": "X"},
    "rating": 5.0,
    "profile_picture": "",
    "phone": "1234567890",
    "email": "vendor@test.com",
    "menu": [FOOD_DETAILS],
}


def side_effect_mongo_mock_from_uuid(
    uuid: UUID, uuid_representation=UuidRepresentation.STANDARD
):
    """Override (Mock) the bson.binary.Binary.from_uuid function to work for mongomock

    Code is copy pasted from the original function,
    but `uuid_representation` is ignored and only code parts as if
    uuid_representation == UuidRepresentation.STANDARD are used
    """
    if not isinstance(uuid, UUID):
        raise TypeError("uuid must be an instance of uuid.UUID")

    subtype = UUID_SUBTYPE
    payload = uuid.bytes

    return Binary(payload, subtype)


@pytest.fixture(autouse=True)
def mongo_uuid():
    with mock.patch.object(
        Binary, "from_uuid", side_effect=side_effect_mongo_mock_from_uuid
    ):
        yield


@pytest.fixture
def vendor_in():
    return {
        **VENDOR_DETAILS,
        "id": "53da6d16-113d-11ef-88b6-e86a64c3b96e",
        "orders": [],
        "queue": {
            "id": "ee6efac7-6f59-4265-bbea-e29e792bf57c",
            "name": "Test vendor",
            "orders": [],
            "current_order": None,
        },
    }


@pytest.fixture
def vendor_out():
    return {
        **VENDOR_DETAILS,
        "id": "53da6d16-113d-11ef-88b6-e86a64c3b96e",
        "orders": [],
        "menu": [
            {
                "collection": "food",
                "id": "6cd4a106-1200-11ef-8495-e86a64c3b96e",
            }
        ],
        "queue": {
            "id": "ee6efac7-6f59-4265-bbea-e29e792bf57c",
            "collection": "queue",
        },
    }


@pytest.fixture
def food_in():
    return FOOD_DETAILS


@pytest.fixture
def food_out():
    _food_out = FOOD_DETAILS.copy()
    del _food_out["id"]

    return _food_out


@pytest.fixture
def anonymous_consumer_in():
    return {
        "id": "1cab0a6c-0e36-11ef-8ffa-e86a64c3b96e",
        "is_anonymous": True,
        "disabled": False,
        "orders": [],
    }


@pytest.fixture
def order(vendor_in, anonymous_consumer_in, food_in):
    return {
        "id": "20240419000056631770",
        "vendor_id": vendor_in["id"],
        "consumer_id": anonymous_consumer_in["id"],
        "foods": [
            {
                "food_id": food_in["id"],
                "quantity": 1,
            }
        ],
        "total_price": food_in["price"]["amount"],
        "status": "waiting",
    }


@pytest.fixture
def next_order(order):
    return {
        **order,
        "status": "processing",
    }


@pytest_asyncio.fixture
async def test_app():
    """App for testing with the lifespan initiated"""

    async with LifespanManager(app=app) as manager:
        yield manager.app


@pytest_asyncio.fixture
async def client(test_app):
    """Client with no overridden dependencies"""

    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def client_with_auth_vendor(test_app, fastapi_dep):
    """
    Client having vendor credentials dependency overridden by a function
    that returns an vendor credentials
    """

    def vendor_credentials_override(credentials: dict | None = None):
        return {
            "sub": "53da6d16-113d-11ef-88b6-e86a64c3b96e",
            "email": "vendor@test.com",
            "phone": "1234567890",
            "is_anonymous": False,
            "user_metadata": {},
        }

    async with AsyncClient(app=test_app, base_url="http://test") as client:
        with fastapi_dep(app).override(
            {
                vendor_credentials: vendor_credentials_override,
            }
        ):
            yield client
