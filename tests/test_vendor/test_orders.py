import pytest
from datetime import datetime
from unittest import mock

from beanie import WriteRules
from fastapi import status

from src.queue import Queue
from src.consumer.models import AnonymousConsumer
from src.vendor.models import Vendor
from src.order.models import Order

from .conftest import API_PREFIX

ORDERS_API_PREFIX = f"{API_PREFIX}/orders"


async def setup(vendor, consumer):
    # Add a vendor to the db
    await Vendor(**vendor).insert(link_rule=WriteRules.WRITE)

    # Add consumer to the db
    await AnonymousConsumer(
        **{
            **consumer,
            "created_at": datetime.now(),
        }
    ).insert()


@pytest.mark.asyncio
async def test_get_all_orders_ok(
    client_with_auth_vendor, vendor_in, anonymous_consumer_in, order
):
    await setup(vendor_in, anonymous_consumer_in)

    response = await client_with_auth_vendor.get(
        f"{ORDERS_API_PREFIX}/all"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

    # Add an order
    vendor = await Vendor.get(vendor_in["id"])
    vendor.orders = [Order(**order)]
    await vendor.save(link_rule=WriteRules.WRITE)

    response = await client_with_auth_vendor.get(
        f"{ORDERS_API_PREFIX}/all"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [order]


@pytest.mark.asyncio
async def test_get_all_orders_not_authenticated(client):
    response = await client.get(f"{ORDERS_API_PREFIX}/all")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_get_all_orders_missing_vendor(client_with_auth_vendor):
    response = await client_with_auth_vendor.get(
        f"{ORDERS_API_PREFIX}/all"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Vendor not found"}


@pytest.mark.asyncio
async def test_get_next_order_ok(
    client_with_auth_vendor,
    vendor_in,
    anonymous_consumer_in,
    order,
    next_order,
):
    await setup(vendor_in, anonymous_consumer_in)

    new_order = Order(**order)

    # Add an order
    vendor = await Vendor.get(vendor_in["id"])
    vendor.orders = [new_order]
    await vendor.save(link_rule=WriteRules.WRITE)

    # Add order to queue
    queue = await Queue.get(vendor_in["queue"]["id"])
    await queue.enqueue(order=new_order)

    async def get_next_order_from_queue_mock(vendor: Vendor) -> Order:
        """Return next order from queue"""
        # Get order from queue
        next_order = await queue.dequeue()
        return next_order

    # The order has been enqueued
    assert len(queue.orders) == 1
    assert queue.current_order is None

    with mock.patch(
        "src.vendor.router.get_next_order_from_queue"
    ) as next_order_mock:
        next_order_mock.side_effect = get_next_order_from_queue_mock

        response = await client_with_auth_vendor.get(
            f"{ORDERS_API_PREFIX}/next"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == next_order

        # Check current_order is set to new_order
        # and orders is empty
        await queue.sync()
        await queue.fetch_link("current_order")
        assert queue.current_order == new_order
        assert len(queue.orders) == 0

        # Also the order in vendor has changed accordingly
        await vendor.sync()
        await vendor.fetch_link("orders")
        assert vendor.orders[0].status == "processing"


@pytest.mark.asyncio
async def test_get_next_order_not_authenticated(client):
    response = await client.get(f"{ORDERS_API_PREFIX}/next")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_get_next_order_missing_vendor(client_with_auth_vendor):
    response = await client_with_auth_vendor.get(
        f"{ORDERS_API_PREFIX}/next"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Vendor not found"}


@pytest.mark.asyncio
async def test_get_next_order_no_orders(
    client_with_auth_vendor,
    vendor_in,
    anonymous_consumer_in,
):
    await setup(vendor_in, anonymous_consumer_in)

    # No order created
    vendor = await Vendor.get(vendor_in["id"])
    await vendor.save(link_rule=WriteRules.WRITE)

    queue = await Queue.get(vendor_in["queue"]["id"])

    async def get_next_order_from_queue_mock(vendor: Vendor) -> Order:
        """Return next order from queue"""
        next_order = await queue.dequeue()
        return next_order

    # Queue is empty
    assert len(queue.orders) == 0
    assert queue.current_order is None

    with mock.patch(
        "src.vendor.router.get_next_order_from_queue"
    ) as next_order_mock:
        next_order_mock.side_effect = get_next_order_from_queue_mock

        response = await client_with_auth_vendor.get(
            f"{ORDERS_API_PREFIX}/next"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() is None

        # Check current_order is None
        # and orders is empty
        await queue.sync()
        await queue.fetch_link("current_order")
        assert queue.current_order is None
        assert len(queue.orders) == 0
