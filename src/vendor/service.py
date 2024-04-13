from pydantic_core._pydantic_core import (
    ValidationError,
    PydanticSerializationError,
)
from pymongo.errors import DuplicateKeyError

from beanie import WriteRules

from src.vendor.models import Vendor, VendorCreate


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
