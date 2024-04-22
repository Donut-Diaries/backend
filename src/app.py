import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


# Setup CORS

LOCALHOST = os.getenv("DD_DEV_HOST", "")

origins = ["https://dd-customer.vercel.app/"]

if LOCALHOST:
    origins.append(LOCALHOST)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
