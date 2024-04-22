from __future__ import annotations

from uuid import UUID, uuid4
from pydantic import Field
from typing_extensions import Annotated, Any, Doc

from beanie import Document, Link, Indexed, WriteRules
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorChangeStream

from src.logger import logger

from src.order.models import Order, STATUS


class Queue(Document):
    """Document representing a vendor's queue"""

    id: Annotated[
        UUID,
        Doc(
            """
            The id of the queue. Defaults to a random uuid4.
            """
        ),
    ] = Field(default_factory=uuid4)

    name: Annotated[
        str,
        Indexed(unique=True),
        Doc(
            """
            The name of the queue. Matches the name of the vendor
            associated with the queue.
            """
        ),
    ]

    orders: Annotated[
        list[Link[Order]],
        Doc(
            """
            List of orders that the vendor has not yet processed and completed
            """
        ),
    ]

    current_order: Annotated[
        Link[Order] | None,
        Doc(
            """
            Order that the vendor is currently processing.
            """
        ),
    ]

    async def enqueue(self, order: Order) -> None:
        """
        Adds a new order to the queue.

        Args:
            order (Order): The order to add to the queue.
            at_front (bool, optional): Whether to add the order at the front.
                Defaults to False.
        """

        # TODO: Add option to add order at the front.

        self.orders.append(order)

        await self.save()

    async def dequeue(self) -> Order:
        """
        Removes the oldest order from the orders list and makes it the current order.

        Returns:
            Order: The order that has been removed from the orders list
        """
        if len(self.orders) > 0:
            self.current_order = self.orders.pop(0)

            await self.fetch_link("current_order")

            self.current_order.status = STATUS.PROCESSING

        else:
            self.current_order = None

        await self.save(link_rule=WriteRules.WRITE)

        return self.current_order

    async def done(self):
        """Marks an order as completed

        The order being completed is `self.current_order` which is the order
        that was being processed if any.
        """

        if self.current_order:
            await self.fetch_link("current_order")
            self.current_order.status = STATUS.COMPLETED

            await self.save(link_rule=WriteRules.WRITE)

    class Settings:
        name = "queue"


class QueueChangeStream:
    """Manage the change stream on the queue collection.

    This change stream is what alerts the websocket to send a message
    to the vendor with an updated count of the current orders.

    Pipeline used for che change stream listens to `update` operation
    and if the updated field is `orders`.
    """

    _instance: Annotated[
        None | __QueueChangeStream,
        Doc(
            """
            An instance of the `__QueueChangeStream` inner class.
            """
        ),
    ] = None

    @classmethod
    async def close(cls):
        """Closes the change stream"""

        if cls._instance:
            await cls._instance.close()

    @classmethod
    def cursor(cls):
        """Returns a cursor to the change stream"""

        if cls._instance:
            return cls._instance.cursor()

    @classmethod
    async def watch(cls, on_change: callable):
        """Creates a change stream and watches for any changes.

        Args:
            on_change (callable): Callable to be called when changes occur.
        """

        if cls._instance:
            await cls._instance.watch(on_change=on_change)

    class __QueueChangeStream:
        def __init__(
            self,
            db: AsyncIOMotorDatabase,
            full_document: str | None = None,
            **kwargs,
        ):
            logger.debug("Creating QueueChangeStream")

            # Listen for the update operation and send change if updated
            # field is orders
            self.pipeline = [
                {
                    "$match": {
                        "operationType": "update",
                        "updateDescription.updatedFields.orders": {
                            "$exists": True
                        },
                    }
                }
            ]

            self.db: Annotated[
                AsyncIOMotorDatabase,
                Doc(
                    """
                    The database where the queue collection is found
                    """
                ),
            ] = db

            self.full_document: Annotated[
                str,
                Doc(
                    """
                    Option to fetch the full document from the change
                    stream watcher.
                    """
                ),
            ] = (
                full_document or "updateLookup"
            )

            self.__watching: Annotated[
                bool,
                Doc(
                    """
                    Whether there is an ongoing watch
                    """
                ),
            ] = False

            self.__change_stream_cursor: Annotated[
                AsyncIOMotorChangeStream | None,
                Doc(
                    """
                    Cursor to iterate over changes in the queue collection
                    """
                ),
            ] = None

        def cursor(self) -> AsyncIOMotorChangeStream:
            """Gets the change stream cursor."""

            pipeline = self.pipeline
            full_document = self.full_document

            if not self.__change_stream_cursor:
                self.__change_stream_cursor = self.db.queue.watch(
                    pipeline=pipeline,
                    full_document=full_document,
                    max_await_time_ms=1,
                )

            return self.__change_stream_cursor

        async def watch(self, on_change: callable, **kwargs):
            """Watches changes for the queue collection and calls
            on_change whenever there is a change.

            Args:
                on_change (callable): The callback to call when there
                    is a change.
            """
            change_stream = self.cursor()

            if not self.__watching:
                self.__watching = True
                logger.info("Starting Queue Change Stream")

                async for change in change_stream:
                    logger.debug("A change occurred")
                    await on_change(change["fullDocument"])

                if change_stream:
                    await self.close()

                self.__watching = False

        async def close(self):
            """Closes the change stream cursor."""

            if self.__change_stream_cursor:
                logger.info("Closing queue change stream")
                self.__watching = False
                await self.__change_stream_cursor.close()
                self.__change_stream_cursor = None

    def __new__(
        cls, db: AsyncIOMotorDatabase | None = None, *args, **kwargs
    ) -> "__QueueChangeStream":
        """Creates a new instance of `__QueueChangeStream`.

        Args:
            db (AsyncIOMotorDatabase | None, optional): A mongodb database.
                Must be provided for the first call. Defaults to None.

        Raises:
            ValueError: If the db is not provided in the first call.
            ValueError: If the db is not of type `AsyncIOMotorDatabase`.

        Returns:
            __QueueChangeStream: An instance of __QueueChangeStream.
        """

        if cls._instance is None and db is None:
            raise ValueError("db must be given for first call")

        elif cls._instance is None and isinstance(db, AsyncIOMotorDatabase):
            cls._instance = cls.__QueueChangeStream(db=db, *args, **kwargs)

        elif cls._instance is None and not isinstance(
            db, AsyncIOMotorDatabase
        ):
            raise ValueError("db must be of type AsyncIOMotorDatabase")

        return cls._instance

    def __getattribute__(self, name: str) -> Any:
        return self._instance.__getattribute__(name)

    def __setattr__(self, name: str, value: Any) -> None:
        self._instance.__setattr__(name, value)
