from enum import StrEnum
from uuid import UUID
from typing_extensions import Annotated, Doc

from beanie import Document
from pydantic import BaseModel, Field, field_validator

from .utils import id_from_datetime

import math


class STATUS(StrEnum):
    """Current status of an order."""

    CANCELED = "canceled"
    WAITING = "waiting"
    PROCESSING = "processing"
    COMPLETED = "completed"


class FoodItem(BaseModel):
    """
    Object representing the food being ordered.

    ### Properties

    * `food_id` - id of the food
    * `quantity` - quantity ordered. Cannot be less than 1.

    Raises:
        ValueError: If the quantity is less than 1.
    """

    food_id: UUID
    quantity: int = 1

    @field_validator("quantity")
    def validate_quantity(cls, quantity: int):
        if quantity < 1:
            raise ValueError("Quantity cannot be less than 1")

        return math.floor(quantity)


class Order(Document):
    """Model representing an order."""

    id: Annotated[
        str,
        Doc(
            """
            Id of the order. Defaults to the current timestamp down to
            micro seconds.
            
            eg: 20240419000056631770
            """
        ),
    ] = Field(default_factory=id_from_datetime)
    vendor_id: Annotated[
        UUID,
        Doc(
            """
            Id of the vendor to receive the order
            """
        ),
    ]
    consumer_id: Annotated[
        UUID,
        Doc(
            """
            Id of the consumer that made the order.
            """
        ),
    ]
    foods: Annotated[
        list[FoodItem],
        Doc(
            """
            List of the foods ordered by the consumer.
            
            Each food is a FoodItem object 
            """
        ),
    ]
    total_price: Annotated[
        float,
        Doc(
            """
            Total price of the food ordered.

            Must match the price calculated using the foods ordered.
            """
        ),
    ]
    status: Annotated[
        STATUS,
        Doc(
            """
            Stage at which the order is currently.
    
            * WAITING -> PROCESSING -> COMPLETED / CANCELED
            """
        ),
    ]

    class Settings:
        name = "order"


class OrderCreate(BaseModel):
    """Model representing values needed to create an Order."""

    vendor_id: UUID
    consumer_id: UUID | None = None
    foods: list[FoodItem]
    total_price: float
    status: STATUS = STATUS.WAITING


class OrderOut(BaseModel):
    """Order output view"""

    id: str
    vendor_id: UUID
    consumer_id: UUID
    foods: list[FoodItem]
    total_price: float
    status: STATUS
