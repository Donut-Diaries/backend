from fastapi import WebSocketDisconnect

from src.logger import logger
from src.websocket_manager import WebsocketManager


async def send_new_order_message(updated_document: dict):
    """
    Sends the new number of orders that the vendor has in the queue

    Args:
        updated_document (dict): The new updated queue as dictionary.
    """

    websocket_manager = WebsocketManager()

    # Name of the queue == Name of vendor and is used to map the websocket
    # in the active connections of the ConnectionManager.
    vendor_name = updated_document.get("name")

    num_orders = len(updated_document["orders"])
    logger.info("Sending message to {0}: {1}".format(vendor_name, num_orders))

    try:
        await websocket_manager.send_personal_message(
            "{0}".format(num_orders), vendor_name
        )
    except WebSocketDisconnect:
        websocket_manager.remove_connection(vendor_name)
