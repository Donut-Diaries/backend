from __future__ import annotations

from typing import Any
from typing_extensions import Annotated, Doc

from fastapi import status, WebSocket
from fastapi.websockets import WebSocketState

from src.logger import logger


class WebsocketManager:
    """
    A singleton class for managing websocket connections in the application.
    """

    _instance: Annotated[
        None | __WebsocketManager,
        Doc(
            """
            An instance of the __WebsocketManager inner class
            """
        ),
    ] = None

    @classmethod
    async def shutdown(cls, name: str):
        if cls._instance:
            await cls._instance.shutdown(name)

    class __WebsocketManager:

        def __init__(self, module_name: str):

            logger.info("Creating WebsocketManager in {}".format(module_name))

            self.__module_name: Annotated[
                str,
                Doc(
                    """
                    Name of the module where the WebsocketManager was
                    instantiated.
                    
                    This helps in making critical functions like `shutdown`
                    are called only in one module.
                    
                    * The functions can still be called if someone explicitly
                    * knows the module where WebsocketManager was instantiated.
                    """
                ),
            ] = module_name

            self.active_connections: Annotated[
                dict[str, WebSocket],
                Doc(
                    """
                    Mapping of the current connected websockets.

                    The name of the websocket has to be unique and match
                    vendor / consumer name so that the connections can be
                    easily retrieved.
                    """
                ),
            ] = {}

        async def connect(self, name: str, websocket: WebSocket):
            """
            Connects a websocket and adds it to the active connections.

            If a websocket with the given name exists it is closed first.

            Args:
                name (str): The name of the connection.
                websocket (WebSocket): The websocket to connect to.
            """

            await websocket.accept()

            # Close websocket mapped to name
            await self.close(name)

            self.active_connections[name] = websocket

        async def close(self, name: str):
            """
            Closes an active connection.

            Args:
                name (str): Name mapping to the connection to close.
            """

            if existing_websocket := self.active_connections.get(name):
                if (
                    existing_websocket.application_state
                    == WebSocketState.CONNECTED
                ):
                    await existing_websocket.close(
                        code=status.WS_1010_MANDATORY_EXT,
                        reason="WM: Duplicate connection",
                    )

        def remove_connection(self, name: str | None = None):
            """
            Removes a connection from the active connections.

            Args:
                name (str | None): The name mapped to the connection to remove.
                    Defaults to None.
            """

            if name:
                try:
                    del self.active_connections[name]
                except KeyError:
                    pass

        async def send_personal_message(self, message: str, name: str):
            """
            Sends a message to the websocket under the given name.
            If the socket is found to be disconnected, it is removed from
            the active_connections

            Args:
                message (str): The message to send
                name (str): The name mapped to the websocket connection
            """

            websocket = self.active_connections.get(name)

            if (
                websocket
                and websocket.application_state == WebSocketState.CONNECTED
            ):
                await websocket.send_text(message)

            elif (
                websocket
                and websocket.application_state == WebSocketState.DISCONNECTED
            ):
                self.remove_connection(name)

            else:
                logger.warning("Invalid connection: {0}".format(name))

        async def broadcast(self, message: str):
            """
            Sends a message to all the connected websockets.

            if a disconnected websocket is encountered, it is removed from
            active connections.

            Args:
                message (str): The message to send.
            """

            for name, connection in self.active_connections.items():
                if connection.application_state == WebSocketState.CONNECTED:
                    await connection.send_text(message)

                elif (
                    connection.application_state == WebSocketState.DISCONNECTED
                ):
                    self.remove_connection(name)

        async def shutdown(self, module_name: str):
            """
            Closes and disconnects all active connections.

            Args:
                module_name (str): name of the module where the WebsocketManager
                    was initialized.

            Raises:
                ValueError: If the module_name is not given or is not of type str
            """

            if not module_name or not isinstance(module_name, str):
                raise ValueError(
                    "module_name must be provided and should be of type str"
                )

            if module_name == self.__module_name:
                logger.info(
                    "Shutting down WebsocketManager from {}".format(
                        module_name
                    )
                )

                for name in self.active_connections.keys():
                    await self.close(name)

                    self.remove_connection(name)
            else:
                logger.warn(
                    "Cannot shutdown WebsocketManager. Shutdown from the module where it was created"
                )

    def __new__(cls, module_name: str | None = None) -> __WebsocketManager:
        """
        Creates a new instance of __WebsocketManager.

        Args:
            module_name (str | None, optional): The name of the module where
                the manager is instantiated. Defaults to None.

        Raises:
            ValueError: If module_name is not a string in first call.

        Returns:
            __WebsocketManager: An instance of __WebsocketManager
        """
        if not cls._instance and isinstance(module_name, str):
            cls._instance = cls.__WebsocketManager(module_name=module_name)

        elif not cls._instance and (
            not module_name or not isinstance(module_name, str)
        ):
            raise ValueError(
                "module_name must be provided in first call and be of type str"
            )

        return cls._instance

    def __getattribute__(self, name: str) -> Any:
        return self._instance.__getattribute__(name)

    def __setattr__(self, name: str, value: Any) -> None:
        self._instance.__setattr__(name, value)
