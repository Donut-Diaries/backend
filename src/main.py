from src.app import app
from src.consumer.router import consumer_router
from src.order.router import router as order_router
from src.vendor.router import router as vendor_router


@app.get("/")
async def root():
    return "donut-diaries-api"


app.include_router(consumer_router)
app.include_router(vendor_router)
app.include_router(order_router)
