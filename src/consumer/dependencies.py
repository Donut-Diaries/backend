from pydantic_core._pydantic_core import ValidationError

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException

from src.auth.jwt_bearer import SupabaseJWTBearer, SupabaseJWTPayload

from src.consumer.models import (
    Consumer,
    AnonymousConsumerCreate,
    SignedConsumerCreate,
)


def consumer_credentials(
    credentials: Annotated[SupabaseJWTPayload, Depends(SupabaseJWTBearer())]
) -> dict:
    """Get dictionary representation of the SupabaseJWTPayload.

    Args:
        credentials (SupabaseJWTPayload): Credentials of the vendor.

    Returns:
        dict: Dictionary of the values in SupabaseJWTPayload
    """
    return credentials.model_dump()


async def get_consumer(
    credentials: dict = Depends(consumer_credentials),
) -> Consumer:
    """Get a consumer from the database.

    Args:
        credentials (dict): Dictionary of the consumer's details from the
            SupabaseJWTPayload.

    Returns:
        Consumer | None: A consumer from the database or None if not found.
    """
    return await Consumer.find_one({"_id": UUID(credentials["sub"])})


async def consumer_exists(
    consumer: Consumer = Depends(get_consumer),
) -> Consumer | None:
    """Validate that a consumer with given credentials exists

    Raises:
        HTTPException: If the consumer does not exist.
    """

    if consumer:
        return consumer

    raise HTTPException(status_code=400, detail="Consumer not found.")


async def consumer_not_exists(
    consumer: Consumer = Depends(get_consumer),
) -> None:
    """Validate that a consumer with given credentials does not exist

    Raises:
        HTTPException: If the consumer already exists.
    """

    if consumer:
        raise HTTPException(status_code=400, detail="Consumer already exists.")


async def validate_anonymous_credentials(
    credentials: dict = Depends(consumer_credentials),
) -> AnonymousConsumerCreate | None:
    """
    Gets credentials from the SupabaseJWT and uses them to create a 
    AnonymousConsumerCreate object.

    Args:
        credentials (dict): Dictionary of the consumer's details from the
            SupabaseJWTPayload.

    Raises:
        HTTPException: If there is a validation error

    Returns:
        AnonymousConsumerCreate: The object containing anonymous consumer
            details that can be used for creation.
    """

    try:
        anonymous_consumer = AnonymousConsumerCreate(
            id=credentials["sub"], **credentials
        )
        return anonymous_consumer
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors()[0])


async def validate_signed_credentials(
    credentials: dict = Depends(consumer_credentials),
) -> SignedConsumerCreate | None:
    """
    Gets credentials from the SupabaseJWT and uses them to create a 
    SignedConsumerCreate object.

    Args:
        credentials (dict): Dictionary of the consumer's details from the
            SupabaseJWTPayload.

    Raises:
        HTTPException: If there is a validation error

    Returns:
        SignedConsumerCreate: The object containing signed consumer
            details that can be used for creation.
    """

    try:
        signed_consumer = SignedConsumerCreate(
            id=credentials["sub"], **credentials
        )
        return signed_consumer
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors()[0])
