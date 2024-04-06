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


async def consumer_exists(
    credentials: Annotated[SupabaseJWTPayload, Depends(SupabaseJWTBearer())]
) -> Consumer | None:
    """Validate that a consumer with given credentials exists

    Args:
        credentials (SupabaseJWTPayload): Credentials of the
            consumer to check.

    Raises:
        HTTPException: If the consumer does not exist.
    """

    consumer: Consumer | None = await Consumer.find_one(
        {"_id": UUID(credentials.model_dump()["sub"])}
    )

    if consumer:
        return consumer

    raise HTTPException(status_code=400, detail="Consumer not found.")


async def consumer_not_exists(
    credentials: Annotated[SupabaseJWTPayload, Depends(SupabaseJWTBearer())]
) -> None:
    """Validate that a consumer with given credentials does not exist

    Args:
        credentials (SupabaseJWTPayload): Credentials of the
            consumer to check.

    Raises:
        HTTPException: If the consumer already exists.
    """

    consumer: Consumer = await Consumer.find_one(
        {"_id": UUID(credentials.model_dump()["sub"])}
    )

    if consumer:
        raise HTTPException(status_code=400, detail="Consumer already exists.")


async def validate_anonymous_credentials(
    credentials: Annotated[SupabaseJWTPayload, Depends(SupabaseJWTBearer())]
) -> AnonymousConsumerCreate | None:
    """

    Args:
        credentials (SupabaseJWTPayload): Credentials of the user from the
            Supabase JWT.

    Raises:
        HTTPException: If there is a validation error

    Returns:
        AnonymousConsumerCreate: The object containing anonymous consumer
            details that can be used for creation.
    """

    try:
        _credentials = credentials.model_dump()
        anonymous_consumer = AnonymousConsumerCreate(
            id=_credentials["sub"], **_credentials
        )
        return anonymous_consumer
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors()[0])


async def validate_signed_credentials(
    credentials: Annotated[SupabaseJWTPayload, Depends(SupabaseJWTBearer())]
) -> SignedConsumerCreate | None:
    """

    Args:
        credentials (SupabaseJWTPayload): Credentials of the user from the
            Supabase JWT.

    Raises:
        HTTPException: If there is a validation error

    Returns:
        SignedConsumerCreate: The object containing signed consumer
            details that can be used for creation.
    """

    try:
        _credentials = credentials.model_dump()
        signed_consumer = SignedConsumerCreate(
            id=_credentials["sub"], **_credentials
        )
        return signed_consumer
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors()[0])
