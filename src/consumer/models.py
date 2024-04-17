from __future__ import annotations

from beanie import Document, Indexed, UnionDoc
from datetime import datetime
from pydantic import EmailStr, Field, model_validator
from typing import Annotated
from uuid import UUID, uuid4


class Consumer(UnionDoc):
    """Consumer DB representation

    This is a UnionDoc containing two types of consumers:
        - `SignedConsumer` - Consumers who have created an account using
            email or phone. Password protected.
        - `AnonymousConsumer` - Consumers who have not linked their accounts
            to an email or phone. Not password protected.

    """

    class Settings:
        name = "consumer"
        class_id = "_class_id"


class ConsumerBase(Document):
    """Base for all consumer classes"""

    id: UUID = Field(default_factory=uuid4)


class SignedConsumer(ConsumerBase):
    """Consumer signed in with an email or phone number.

    Child to the `Consumer` UnionDoc.

    Documents of this class are stored in the `consumer` collection
    as set by the parent and have a `_class_id = 'SignedConsumer'`
    """

    email: Annotated[str, Indexed(EmailStr, unique=True)]
    phone: str
    is_anonymous: bool
    disabled: bool
    created_at: datetime
    updated_at: datetime

    def __repr__(self) -> str:
        return f"<Consumer {self.email}>"

    def __str__(self) -> str:
        return self.email

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Consumer):
            return self.email == other.email
        return False

    @classmethod
    async def by_email(cls, email: str) -> Consumer | None:
        """Get a user by email."""
        return await cls.find_one(cls.email == email)

    class Settings:
        union_doc = Consumer


class SignedConsumerCreate(ConsumerBase):
    """Model used when creating new`SignedConsumer`

    This model is also used when making a previous `AnonymousConsumer`
    a `SignedConsumer`.
    """

    email: Annotated[str | None, Indexed(EmailStr, unique=True)] = None
    phone: str = ""
    is_anonymous: bool = False
    disabled: bool = False
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    @model_validator(mode="after")
    def check_phone_or_email_provided(self):
        if self.email is None and self.phone == "":
            raise ValueError("Must provide email or phone")
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "email": "one@one.com",
                "phone": "1234",
                "is_anonymous": False,
                "disabled": False,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }
        }


class SignedConsumerUpdate(Document):
    """Model used when updating `SignedConsumer`"""

    email: Annotated[str | None, Indexed(EmailStr, unique=True)] = None
    phone: str | None = None
    is_anonymous: bool | None = None
    disabled: bool | None = None


class SignedConsumerOut(ConsumerBase):
    """Model used as the return type for `SignedConsumer`"""

    email: Annotated[str, Indexed(str, unique=True)] = ""
    phone: str = ""
    is_anonymous: bool = False
    disabled: bool = False


class AnonymousConsumer(ConsumerBase):
    """Consumer not signed in with an email or phone number.

    Child to the `Consumer` UnionDoc.

    Documents of this class are stored in the `consumer` collection
    as set by the parent and have a `_class_id = 'AnonymousConsumer'`
    """

    is_anonymous: bool
    disabled: bool
    created_at: datetime

    class Settings:
        union_doc = Consumer


class AnonymousConsumerCreate(ConsumerBase):
    """Model used when creating a new `AnonymousConsumer`"""

    is_anonymous: bool = True
    disabled: bool = False
    created_at: datetime = datetime.now()


class AnonymousConsumerOut(ConsumerBase):
    """Model used as the return type for `AnonymousConsumer`"""

    is_anonymous: bool = True
    disabled: bool = False
