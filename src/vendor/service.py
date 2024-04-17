from pydantic_core._pydantic_core import (
    ValidationError,
    PydanticSerializationError,
)
from pymongo.errors import DuplicateKeyError

from beanie import WriteRules

from src.vendor.models import (
    Vendor,
    VendorCreate,
    FoodCreate,
    Food,
    FoodUpdate,
)


async def create_vendor(vendor_details: VendorCreate) -> Vendor | None:
    try:

        vendor = Vendor(**vendor_details.model_dump())
        await vendor.insert(link_rule=WriteRules.WRITE)

        return vendor
    except DuplicateKeyError:
        pass
    except ValidationError as e:
        print(e.errors()[0])
    except PydanticSerializationError as e:
        print(e)


async def insert_food(
    food_create: FoodCreate | list[FoodCreate], vendor: Vendor
) -> list[Food]:
    """
    Adds new food to the vendor's menu.

    Args:
        food_create (FoodCreate | list[FoodCreate]): A single food or list of foods.
        vendor (Vendor): Vendor to add the food to.

    Returns:
        list[Food]: A list of the newly added foods.
    """

    new_foods = []
    new_food = None

    if isinstance(food_create, list):
        new_foods = [Food(**_food.model_dump()) for _food in food_create]
        vendor.menu.extend(new_foods)
    else:
        new_food = Food(**food_create.model_dump())
        vendor.menu.append(new_food)

    await vendor.save(link_rule=WriteRules.WRITE)

    return [new_food] if new_food else new_foods


async def update_food(food_update: FoodUpdate, old_food: Food) -> Food:
    """
    Updates vendor's food in the menu.

    Args:
        food_update (FoodUpdate): The data to update the food with
        old_food (Food): The food to be updated

    Returns:
        Food: The updated food
    """

    new_food_details = {
        key: value for key, value in food_update.model_dump().items() if value
    }

    await old_food.update({"$set": {**new_food_details}})

    return old_food


async def delete_food(food: Food, vendor: Vendor) -> None:
    """
    Deletes food from the vendor's menu.

    Args:
        food (Food): The food to delete
        vendor (Vendor): The vendor to delete the food from
    """

    for _food in vendor.menu:
        if _food.to_dict()["id"] == str(food.id):
            vendor.menu.remove(_food)
            await vendor.save()
            break

    await food.delete()
