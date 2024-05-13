from pydantic_core import ErrorDetails

from fastapi import APIRouter, Depends, status

from src.auth.jwt_bearer import SupabaseJWTBearer
from src.consumer.dependencies import (
    consumer_exists,
    consumer_not_exists,
    validate_anonymous_credentials,
    validate_signed_credentials,
)
from src.consumer.schema import HTTPError
from src.consumer.models import (
    AnonymousConsumer,
    AnonymousConsumerCreate,
    AnonymousConsumerOut,
    SignedConsumer,
    SignedConsumerCreate,
    SignedConsumerOut,
)
from src.consumer.service import (
    create_anonymous_consumer,
    create_signed_consumer,
)

consumer_router = APIRouter(
    prefix="/consumer",
    tags=["consumer"],
    dependencies=[Depends(SupabaseJWTBearer)],
)


@consumer_router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=AnonymousConsumerOut | SignedConsumerOut,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": HTTPError,
            "description": "Consumer does not exist",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": HTTPError,
            "description": "Forbidden",
        },
    },
)
def me(
    consumer: AnonymousConsumer | SignedConsumer = Depends(consumer_exists),
) -> AnonymousConsumerOut | SignedConsumerOut:
    return consumer


@consumer_router.post(
    "/create/anonymous",
    dependencies=[Depends(consumer_not_exists)],
    status_code=status.HTTP_201_CREATED,
    response_model=AnonymousConsumerOut,
    # response_model_exclude="_id",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": HTTPError,
            "description": "Consumer already created",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": HTTPError,
            "description": "Forbidden",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ErrorDetails,
            "description": "Validation Error",
        },
    },
)
async def create_anonymous_customer(
    anonymous_consumer: AnonymousConsumerCreate = Depends(
        validate_anonymous_credentials
    ),
) -> AnonymousConsumerOut:
    consumer = await create_anonymous_consumer(anonymous_consumer)

    return consumer


@consumer_router.post(
    "/create/signed",
    dependencies=[Depends(consumer_not_exists)],
    status_code=status.HTTP_201_CREATED,
    response_model=SignedConsumerOut,
    # response_model_exclude="_id",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": HTTPError,
            "description": "Consumer already created",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": HTTPError,
            "description": "Forbidden",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ErrorDetails,
            "description": "Validation Error",
        },
    },
)
async def create_signed_customer(
    signed_consumer: SignedConsumerCreate = Depends(
        validate_signed_credentials
    ),
) -> SignedConsumerOut:
    consumer = await create_signed_consumer(signed_consumer)

    return consumer
