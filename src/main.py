from src.app import app

from src.consumer.router import consumer_router


@app.get("/")
async def root():
    return "donut-diaries-api"


app.include_router(consumer_router)
