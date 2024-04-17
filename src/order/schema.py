from uuid import UUID

from pydantic import BaseModel, Field

from src.order.models import OrderCreate
from src.consumer.models import AnonymousConsumer, SignedConsumer
from src.vendor.models import Vendor


class FoodPriceView(BaseModel):
    """
    Object for projecting a Food object into the `id` and `price`.
    The `price` is the amount only, i.e `$price.amount` from the `Food`
    """

    id: UUID = Field(alias="_id")
    price: float

    class Settings:
        projection = {"_id": 1, "price": "$price.amount"}


class OrderVendorConsumer(BaseModel):
    """
    Model of an `order_create` and the related `vendor` and `consumer`.

    Used when creating a new order.
    """

    order_create: OrderCreate
    vendor: Vendor
    consumer: AnonymousConsumer | SignedConsumer


class HTTPError(BaseModel):
    detail: str
