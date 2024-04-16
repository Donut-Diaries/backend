from collections import defaultdict
from uuid import UUID
from typing import Annotated

from fastapi import Depends, HTTPException
from beanie.operators import In

from src.auth.jwt_bearer import SupabaseJWTBearer, SupabaseJWTPayload

from src.order.models import OrderCreate, FoodItem
from src.order.schema import FoodPriceView, OrderVendorConsumer

from src.consumer.models import Consumer
from src.vendor.models import Vendor, Food


def consumer_id(
    credentials: Annotated[SupabaseJWTPayload, Depends(SupabaseJWTBearer())]
) -> UUID:
    """
    Gets the consumer's id from the Supabase JWT.

    Args:
        credentials (SupabaseJWTPayload): Credentials of the vendor.

    Returns:
        UUID: Id of the consumer as UUID
    """
    id = credentials.model_dump()["sub"]

    return id if isinstance(id, UUID) else UUID(id)


async def get_consumer_from_id(consumer_id: UUID) -> Consumer | None:
    """
    Gets the consumer with the given id.

    Args:
        consumer_id (UUID): The id of the consumer

    Raises:
        HTTPException: If there is no consumer with the given id

    Returns:
        Consumer | None: The consumer if found, else None
    """
    consumer: Consumer = await Consumer.find_one({"_id": consumer_id})

    if not consumer:
        raise HTTPException(detail="Consumer does not exist", status_code=400)

    return consumer


async def get_vendor_from_id(vendor_id: UUID) -> Vendor | None:
    """
    Gets the vendor with the given id.


    Args:
        vendor_id (UUID): The id of the vendor.

    Raises:
        HTTPException: If the vendor does not exist

    Returns:
        Vendor | None: The vendor if found, else None
    """
    vendor: Vendor = await Vendor.get(vendor_id)

    if not vendor:
        raise HTTPException(detail="vendor does not exist", status_code=400)

    return vendor


async def validate_foods(foodItems: list[FoodItem], vendor: Vendor) -> None:
    """
    Validates that the given foods are found in the vendor's menu.

    Args:
        foodItems (list[FoodItem]): List of the foods
        vendor (Vendor): The vendor to check from

    Raises:
        HTTPException: If a food is not found in the vendor's menu.
    """

    vendor_food_ids = [food.to_dict()["id"] for food in vendor.menu]
    food_ids = [food.food_id for food in foodItems]

    for food_id in food_ids:
        if str(food_id) not in vendor_food_ids:
            raise HTTPException(
                detail="Invalid food with id: {}".format(food_id),
                status_code=400,
            )


async def validate_total_price(total_price: float, food_items: list[FoodItem]):
    """
    Validates that the total price in the order matches with the ordered foods.

    Args:
        total_price (float): The total price as in the order
        food_items (list[FoodItem]): The foods in the order

    Raises:
        HTTPException: If the calculated price from the foods does not match
            the provided total price.
    """
    food_ids = [food.food_id for food in food_items]

    foods: Food = (
        await Food.find(In(Food.id, food_ids)).project(FoodPriceView).to_list()
    )

    food_items_dict = {food.food_id: food.quantity for food in food_items}

    _total_price: float = sum(
        [food.price * food_items_dict[food.id] for food in foods]
    )

    if total_price != _total_price:
        raise HTTPException(status_code=400, detail="Food prices don't match")


def remove_duplicates(food_items: list[FoodItem]):
    """
    Removes duplicates from the foods.

    Args:
        food_items (list[FoodItem]): List of foods to clean
    """

    def default_value() -> int:
        """Returns default value for the defaultdict"""
        return 0

    food_items_dict = defaultdict(default_value)

    for food_item in food_items:
        food_items_dict[food_item.food_id] += food_item.quantity

    return [
        FoodItem(food_id=key, quantity=value)
        for key, value in food_items_dict.items()
    ]


async def validate_order_create(
    order_create: OrderCreate, consumer_id: UUID = Depends(consumer_id)
) -> OrderVendorConsumer | None:
    """
    Validates the values provided to create an order.

    Args:
        order_create (OrderCreate): The order body.

    Returns:
        OrderVendorConsumer | None: An object of the order_create,
            consumer and vendor
    """

    order_create.consumer_id = consumer_id

    consumer: Consumer = await get_consumer_from_id(consumer_id)

    vendor: Vendor = await get_vendor_from_id(order_create.vendor_id)

    order_create.foods = remove_duplicates(order_create.foods)

    await validate_foods(order_create.foods, vendor=vendor)

    await validate_total_price(order_create.total_price, order_create.foods)

    return OrderVendorConsumer(
        order_create=order_create, vendor=vendor, consumer=consumer
    )
