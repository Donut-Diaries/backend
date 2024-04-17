from pymongo.errors import DuplicateKeyError


from src.consumer.models import (
    AnonymousConsumer,
    AnonymousConsumerCreate,
    SignedConsumer,
    SignedConsumerCreate,
)


async def create_anonymous_consumer(
    anonymous_consumer: AnonymousConsumerCreate,
) -> AnonymousConsumer:
    """Create a new anonymous consumer.

    Args:
        credentials (SupabaseJWTPayload): Credentials of the user from the
            Supabase JWT.

    Returns:
        AnonymousConsumer: The created anonymous consumer.
    """
    try:
        consumer: AnonymousConsumer = AnonymousConsumer(
            **anonymous_consumer.model_dump(), orders=[]
        )
        await consumer.insert()

        return consumer
    except DuplicateKeyError:
        pass


async def create_signed_consumer(
    signed_consumer: SignedConsumerCreate,
) -> SignedConsumer:
    """Create a new signed consumer.

    Args:
        credentials (SupabaseJWTPayload): Credentials of the user from the
            Supabase JWT.

    Returns:
        SignedConsumer: The created signed consumer.
    """

    try:
        consumer: SignedConsumer = SignedConsumer(
            **signed_consumer.model_dump(), orders=[]
        )
        await consumer.insert()

        return consumer
    except DuplicateKeyError:
        pass
