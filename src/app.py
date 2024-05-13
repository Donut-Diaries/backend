import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.database import init_db
from src.queue import QueueChangeStream
from src.service import send_new_order_message
from src.websocket_manager import WebsocketManager


DESCRIPTION = """
Donut-Diaries API
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(app)

    # WebsocketManager that can only be shutdown in this module
    WebsocketManager(__name__)

    # Initialize new queue change stream
    QueueChangeStream(app.db)

    # Create task to continuously watch the query collection
    task = asyncio.create_task(
        QueueChangeStream.watch(on_change=send_new_order_message)
    )

    yield

    # Cancel the query collection watcher task
    task.cancel()

    # Ensure queue change stream is closed.
    await QueueChangeStream.close()

    # Close all open websockets
    await WebsocketManager.shutdown()

    # Close the database connection
    app.client.close()

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
