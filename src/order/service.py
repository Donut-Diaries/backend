from beanie import WriteRules

from src.order.schema import OrderVendorConsumer
from src.order.models import Order

from src.vendor.models import Vendor

from src.queue import Queue


async def create_order(new_order: OrderVendorConsumer) -> Order:
    """
    Creates a new order and adds it to the relevant consumer and
    vendor.

    Args:
        new_order (OrderVendorConsumer): Object containing the `order_create`,
            `consumer` and `vendor` objects.

    Returns:
        Order: The new order.
    """

    order: Order = Order(**new_order.order_create.model_dump())

    new_order.consumer.orders.append(order)
    # Save the new consumer.
    await new_order.consumer.save()

    vendor = new_order.vendor

    vendor.orders.append(order)

    # Add order to the queue
    await enqueue_order(vendor, order)

    # Save vendor and write the new order and queue to the database
    await vendor.save(link_rule=WriteRules.WRITE)

    return order


async def fetch_queue(vendor: Vendor) -> Queue:
    """
    Fetches the queue from the link stored in vendor.

    Args:
        vendor (Vendor): The vendor to fetch their queue.

    Returns:
        Queue: The fetched queue.
    """

    # Fetch queue from link
    await vendor.fetch_link("queue")

    # Now vendor.queue is an instance of Queue instantiated
    # with the data from the linked queue

    return vendor.queue


async def enqueue_order(vendor: Vendor, order: Order) -> None:
    """
    Adds an order to the vendor's queue.

    Args:
        vendor (Vendor): The vendor to add to their queue
        order (Order): The order to add to the vendor's queue
    """

    queue = await fetch_queue(vendor)

    # Add the order at at the end of queue
    await queue.enqueue(order=order)
