from fastapi import FastAPI

from src.consumer.router import consumer_router

app = FastAPI()


@app.get("/")
async def root():
    return "donut-diaries-api"


app.include_router(consumer_router)
