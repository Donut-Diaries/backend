from enum import StrEnum
from uuid import UUID, uuid4
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    model_validator,
    field_validator,
)
from typing_extensions import Annotated, Doc

from beanie import Document, Indexed, Link


class STATUS(StrEnum):
    """Status of a vendor.

    - Open
    - Closed

    """

    OPEN = "Open"
    CLOSED = "Closed"


class Location(BaseModel):
    """Location of the vendor"""

    street: str
    town: str


class FoodPrice(BaseModel):
    """Price of food. Includes `amount` and `currency`."""

    amount: float
    currency: str


class Food(Document):
    """Food document model.

    Stored in the `food` collection.
    """

    # TODO: Add backlink to the vendor / id of the vendor

    id: UUID = Field(alias="_id", default_factory=uuid4)

    name: Annotated[str, Doc("""Name of the food. Must be provided""")]
    description: Annotated[
        str | None, Doc("""Short description of the food""")
    ]

    picture: Annotated[
        list[str] | None,
        Doc(
            """
            List of links to pictures of the food.
            """
        ),
    ]
    price: Annotated[
        FoodPrice,
        Doc(
            """
            Price of the food.
            
            Currency will depend on user locale.
            """
        ),
    ]
    available: Annotated[
        bool,
        Doc(
            """
            Whether the food is available for purchase
            """
        ),
    ]
    ttp: Annotated[
        int,
        Doc(
            """
            Time in minutes taken to prepare the food.
            """
        ),
    ]
    ingredients: Annotated[
        list[str] | None,
        Doc(
            """
            List of the various ingredients that go into making the food.
            """
        ),
    ]

    # TODO: Add Category Enum to provide options for the food category
    category: Annotated[
        list[str] | None,
        Doc(
            """
            Category of the food. ie. drink, cake etc.
            
            A food can have more than one category.
            """
        ),
    ]

    @field_validator("name")
    def validate_name(cls, name: str):
        _name = name.strip()

        if len(_name) == 0:
            raise ValueError("Cannot provide empty food name")

        return _name

    class Settings:
        name = "food"


class FoodCreate(BaseModel):
    name: str
    description: str | None = None
    picture: list[str] | None = None
    price: FoodPrice
    available: bool = True
    ttp: int = 0
    ingredients: list[str] | None = None
    category: list[str] | None = None


class Vendor(Document):
    """Vendor document model.

    Stored in the `vendor` collection.
    """

    id: UUID = Field(alias="_id", default_factory=uuid4)

    name: Annotated[
        str,
        Doc(
            """
        Name of the vendor's business / shop.
        
        Displayed as the vendor's username and is preferably be the
        name of the shop.
        """
        ),
    ]

    email: Annotated[
        str, Indexed(EmailStr, unique=True), Doc("""Email of the vendor""")
    ]

    phone: Annotated[str, Doc("""Phone number of the vendor""")]

    location: Annotated[Location, Doc("""Place where the shop is located""")]

    description: Annotated[
        str | None,
        Doc(
            """
            Short description of the establishment
            """
        ),
    ]

    profile_picture: Annotated[
        str | None, Doc("""Link to the profile picture""")
    ]

    rating: Annotated[float | None, Doc("""Rating of the establishment""")]

    status: Annotated[
        STATUS,
        Doc(
            """
            If the vendor is open or closed.
            """
        ),
    ]

    menu: Annotated[
        list[Link[Food]],
        Doc(
            """
            List of references to the vendor's foods.
            """
        ),
    ]

    @field_validator("name")
    def validate_name(cls, name: str):
        _name = name.strip()

        if len(_name) == 0:
            raise ValueError("Cannot provide empty vendor name")

        return _name

    class Settings:
        name = "vendor"


class VendorCreate(BaseModel):
    """Model used to represent data required to create a `Vendor`.

    Raises:
        ValueError: If both email and phone are not given.
    """

    model_config = ConfigDict(validate_assignment=True)

    id: UUID | None = None
    name: str
    email: Annotated[str, EmailStr] = None
    phone: str = None
    location: Location
    description: str | None = None
    profile_picture: str | None = None
    rating: float = 0
    status: STATUS = STATUS.CLOSED
    menu: list[FoodCreate] | None = None

    @model_validator(mode="after")
    def check_phone_or_email_provided(self):
        if not self.email and not self.phone:
            raise ValueError("Must provide email or phone")

        if self.name.strip() == "":
            raise ValueError("Cannot provide empty vendor name")

        return self


class VendorUpdate(BaseModel):
    """Model representing data required when updating a `Vendor`."""

    name: str | None = None
    email: Annotated[str | None, EmailStr] = None
    phone: str | None = None
    location: Location | None = None
    description: str | None = None
    profile_picture: str | None = None
    rating: float | None = None
    status: STATUS = STATUS.CLOSED
    menu: list[Food] | None = None


class VendorOut(BaseModel):
    """Model used as return type for `Vendor`."""

    id: UUID
    name: str
    email: str
    phone: str
    location: Location
    description: str
    profile_picture: str
    rating: float
    status: STATUS
    menu: list[Link[Food]]
