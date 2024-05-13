import pytest
import pytest_asyncio

from asgi_lifespan import LifespanManager
from httpx import AsyncClient

from src.main import app
from src.consumer.dependencies import consumer_credentials


@pytest.fixture(scope="session")
def anonymous_consumer_out():
    """The expected anonymous consumer output"""

    return {
        "_id": "1cab0a6c-0e36-11ef-8ffa-e86a64c3b96e",
        "disabled": False,
        "is_anonymous": True,
        "orders": [],
    }


@pytest.fixture(scope="session")
def signed_consumer_out():
    """The expected signed consumer output"""

    return {
        "_id": "536bcfae-1120-11ef-b83a-e86a64c3b96e",
        "disabled": False,
        "is_anonymous": False,
        "orders": [],
    }


@pytest.fixture(scope="session")
def signed_consumer_created_out():
    """The expected signed consumer output"""

    return {
        "_id": "536bcfae-1120-11ef-b83a-e86a64c3b96e",
        "disabled": False,
        "email": "one@test.com",
        "phone": "0100000000",
        "is_anonymous": False,
        "orders": [],
    }


@pytest.fixture(scope="session")
def anonymous_consumer_in():
    return {
        "id": "1cab0a6c-0e36-11ef-8ffa-e86a64c3b96e",
        "is_anonymous": True,
        "disabled": False,
        "orders": [],
    }


@pytest.fixture(scope="session")
def signed_consumer_in():
    return {
        "id": "536bcfae-1120-11ef-b83a-e86a64c3b96e",
        "email": "one@test.com",
        "phone": "0100000000",
        "is_anonymous": False,
        "disabled": False,
        "orders": [],
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
async def client_anon_consumer(test_app, fastapi_dep):
    """
    Client having consumer credentials dependency overridden by a function
    that returns an anonymous consumer credentials
    """

    def anon_consumer_credentials_override(credentials: dict | None = None):
        return {
            "sub": "1cab0a6c-0e36-11ef-8ffa-e86a64c3b96e",
            "email": "",
            "phone": "",
            "is_anonymous": True,
            "user_metadata": {},
        }

    async with AsyncClient(app=test_app, base_url="http://test") as client:
        with fastapi_dep(app).override(
            {
                consumer_credentials: anon_consumer_credentials_override,
            }
        ):
            yield client


@pytest_asyncio.fixture
async def client_signed_consumer(test_app, fastapi_dep):
    """
    Client having consumer credentials dependency overridden by a function
    that returns a signed consumer consumer credentials
    """

    def signed_consumer_credentials_override(credentials: dict | None = None):
        return {
            "sub": "536bcfae-1120-11ef-b83a-e86a64c3b96e",
            "email": "one@test.com",
            "phone": "0100000000",
            "is_anonymous": False,
            "user_metadata": {},
        }

    async with AsyncClient(app=test_app, base_url="http://test") as client:
        with fastapi_dep(app).override(
            {
                consumer_credentials: signed_consumer_credentials_override,
            }
        ):
            yield client
