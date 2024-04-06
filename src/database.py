from fastapi import FastAPI
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from src.config import CONFIG
from src.consumer.models import Consumer, AnonymousConsumer, SignedConsumer


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
    app.db = AsyncIOMotorClient(get_mongodb_uri()).donut_diaries
    await init_beanie(
        app.db, document_models=[Consumer, AnonymousConsumer, SignedConsumer]
    )
