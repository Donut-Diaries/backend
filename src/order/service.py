from beanie import WriteRules

from src.order.schema import OrderVendorConsumer
from src.order.models import Order


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

    new_order.vendor.orders.append(order)
    # Save vendor and write the new order to the database
    await new_order.vendor.save(link_rule=WriteRules.WRITE)

    return order
