from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.database import init_db


DESCRIPTION = """
Donut-Diaries API
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(app)
    yield


app = FastAPI(
    title="Donut-Diaries API",
    description=DESCRIPTION,
    version="0.1.0",
    license_info={
        "name": "MIT",
        "url": "https://github.com/Donut-Diaries/backend/blob/main/LICENSE",
    },
    lifespan=lifespan,
)
