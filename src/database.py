from fastapi import FastAPI
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from mongomock_motor import AsyncMongoMockClient

from src.config import CONFIG
from src.logger import logger
from src.consumer.models import Consumer, AnonymousConsumer, SignedConsumer

from src.vendor.models import Vendor, Food

from src.order.models import Order

from src.queue import Queue


def get_mongodb_uri():
    if CONFIG.MONGODB_URI:
        return CONFIG.MONGODB_URI

    return (
        "{}://{}:{}@{}:{}".format(
            CONFIG.MONGODB_SCHEME,
            CONFIG.MONGODB_USER,
            CONFIG.MONGODB_PW,
            CONFIG.MONGODB_HOST,
            CONFIG.MONGODB_PORT,
        )
        if CONFIG.MONGODB_PW and CONFIG.MONGODB_USER
        else "{}://{}:{}".format(
            CONFIG.MONGODB_SCHEME,
            CONFIG.MONGODB_HOST,
            CONFIG.MONGODB_PORT,
        )
    )


async def init_db(app: FastAPI):
    """Initialize database"""

    logger.info("Initializing database")

    uri = get_mongodb_uri()

    app.client = (
        AsyncIOMotorClient(uri, uuidRepresentation="standard")
        if CONFIG.ENVIRONMENT != "test"
        else AsyncMongoMockClient(uri, uuidRepresentation="standard")
    )

    if isinstance(app.client, AsyncMongoMockClient):
        logger.debug("Using test Mongo Client")

    app.db = app.client.donut_diaries

    await init_beanie(
        app.db,
        document_models=[
            Consumer,
            AnonymousConsumer,
            SignedConsumer,
            Vendor,
            Food,
            Order,
            Queue,
        ],
    )
