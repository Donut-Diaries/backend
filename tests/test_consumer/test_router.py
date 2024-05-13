import pytest
from fastapi import status
from datetime import datetime

from src.consumer.models import AnonymousConsumer, SignedConsumer


@pytest.mark.asyncio
async def test_get_consumer_not_authenticated(client):

    response = await client.get("/consumer/me")

    assert response is not None
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_anonymous_consumer(
    client_anon_consumer,
    anonymous_consumer_in,
    anonymous_consumer_out,
):
    # insert anonymous consumer.
    await AnonymousConsumer(
        **{
            **anonymous_consumer_in,
            "created_at": datetime.now(),
        }
    ).insert()

    response = await client_anon_consumer.get("/consumer/me")

    assert response is not None
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == anonymous_consumer_out


@pytest.mark.asyncio
async def test_create_anonymous_consumer(
    client_anon_consumer,
    anonymous_consumer_out,
):

    response = await client_anon_consumer.post("/consumer/create/anonymous")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == anonymous_consumer_out


@pytest.mark.asyncio
async def test_duplicate_anonymous_consumer(
    client_anon_consumer,
    anonymous_consumer_out,
):

    response = await client_anon_consumer.post("/consumer/create/anonymous")

    assert response is not None
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == anonymous_consumer_out

    response1 = await client_anon_consumer.post("/consumer/create/anonymous")

    assert response1 is not None
    assert response1.status_code == status.HTTP_400_BAD_REQUEST
    assert response1.json() == {"detail": "Consumer already exists."}


@pytest.mark.asyncio
async def test_get_signed_consumer(
    client_signed_consumer,
    signed_consumer_in,
    signed_consumer_out,
):
    # Insert a signed consumer.
    await SignedConsumer(
        **{
            **signed_consumer_in,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
    ).insert()

    response = await client_signed_consumer.get("/consumer/me")

    assert response is not None
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == signed_consumer_out


@pytest.mark.asyncio
async def test_create_signed_consumer(
    client_signed_consumer,
    signed_consumer_created_out,
):
    response = await client_signed_consumer.post("/consumer/create/signed")

    assert response is not None
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == signed_consumer_created_out


@pytest.mark.asyncio
async def test_duplicate_signed_consumer(
    client_signed_consumer,
    signed_consumer_created_out,
):
    response = await client_signed_consumer.post("/consumer/create/signed")

    assert response is not None
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == signed_consumer_created_out

    response1 = await client_signed_consumer.post("/consumer/create/signed")

    assert response1 is not None
    assert response1.status_code == status.HTTP_400_BAD_REQUEST
    assert response1.json() == {"detail": "Consumer already exists."}
