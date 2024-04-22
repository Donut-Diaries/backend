from uuid import UUID, uuid4
from pydantic import Field
from typing_extensions import Annotated, Doc

from beanie import Document, Link, Indexed, WriteRules

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
