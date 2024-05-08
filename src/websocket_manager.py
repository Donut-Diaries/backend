from __future__ import annotations

import inspect
from typing import Any

from fastapi import WebSocket, status
from fastapi.websockets import WebSocketState
from typing_extensions import Annotated, Doc

from src.logger import logger


class ModuleNameNotFoundError(Exception):
    """
    Exception raised if the module_name cannot be determined from the stack.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        self.message = "module_name could not be determined from the stack"


class WebsocketManager:
    """
    A singleton class for managing websocket connections in the application.

    ## Example

        ```python
        from src.websocket_manager import WebsocketManager


        # Explicitly providing the module name by passing __name__

        manager = WebsocketManager(__name__) # Instantiation
        manager.shutdown(__name__)  # Will only work if __name__ is same as
                                    # the one used in instantiation.


        # Not providing __name__ and letting the class get it from stack

        manager = WebsocketManager() # module name is gotten from stack
        manager.shutdown() # Also gotten from stack. Will only work if the
                           # inferred module name is same as from instantiation
        ```
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
    async def shutdown(cls, module_name: str | None = None):
        """Closes and disconnects all active connections.

        If `module_name` is None, it is inferred from the module calling
        this method. That means that this method will only work if called
        from the module where the WebsocketManager was instantiated or if
        the `module_name` is provided while calling from a different file.

        Args:
            module_name (str | None, optional): Name of the module where the
                WebsocketManager was instantiated. Defaults to None.
        """
        if cls._instance:
            await cls._instance.shutdown(module_name)

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

        async def shutdown(self, module_name: str | None = None):
            """
            Closes and disconnects all active connections.

            If `module_name` is None, it is inferred from the module calling
            this method. That means that this method will only work if called
            from the module where the WebsocketManager was instantiated or if
            the `module_name` is provided while calling from a different file.

            Args:
                module_name (str | None): name of the module where the WebsocketManager
                    was initialized. Defaults to None.

            Raises:
                TypeError: If the module_name is given and is not of type str
                ModuleNameNotFoundError: If the module_name is None and cannot be
                    gotten from the stack
            """

            if module_name and not isinstance(module_name, str):
                raise TypeError("module_name must be of type str or None")

            if not module_name:
                # Get module name from stack
                module_name = self.__get_calling_module_name()

            if not module_name:
                logger.warn(
                    "Cannot shutdown WebsocketManager. module_name could not be found."
                )
                raise ModuleNameNotFoundError

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

        @staticmethod
        def __get_calling_module_name() -> str | None:
            """
            Gets the name of the module where a method was called from
            by checking the stack.
            """

            def _module_name(obj: object) -> str | None:
                if module := inspect.getmodule(obj):
                    return module.__name__

            module_name: str | None = None
            index = 1

            frm = inspect.stack()[index]
            module_name = _module_name(frm[0])

            if module_name:
                # Loop over all stack records from this module.
                while module_name == __name__:
                    index += 1
                    try:
                        frm = inspect.stack()[index]
                        module_name = _module_name(frm[0])
                    except IndexError:
                        # Original call was from this module
                        break

            logger.debug("{} calling WebsocketManager".format(module_name))

            return module_name

    def __new__(
        cls, module_name: str | None = None
    ) -> __WebsocketManager | None:
        """
        Creates a new instance of __WebsocketManager.

        Args:
            module_name (str | None, optional): The name of the module where
                the manager is instantiated. Defaults to None. If it is `None`,
                it is inferred from the stack by getting the module calling the
                class.

        Raises:
            TypeError: If module_name is provided and is not a string.

        Returns:
            __WebsocketManager: An instance of __WebsocketManager


        ## Example

        ```python
        from src.websocket_manager import WebsocketManager


        # Explicitly providing the module name by passing __name__

        manager = WebsocketManager(__name__)    # Instantiation
        manager.shutdown(__name__)  # Will only work if __name__ is same as the one used in instantiation.


        # Not providing __name__ and letting the class get it from stack

        manager = WebsocketManager() # module name is gotten from stack
        manager.shutdown() # Also gotten from stack. Will only work if the
                           # inferred module name is same as from instantiation
        ```
        """

        if not cls._instance and isinstance(module_name, str):
            cls._instance = cls.__WebsocketManager(module_name=module_name)

        elif not cls._instance and not module_name:
            # Use module name from the stack
            module_name = cls.__WebsocketManager.__get_calling_module_name()
            cls._instance = cls.__WebsocketManager(module_name=module_name)

        elif not cls._instance and (
            module_name and not isinstance(module_name, str)
        ):
            raise TypeError(
                "module_name must be provided be of type str or None"
            )

        return cls._instance

    def __getattribute__(self, name: str) -> Any:
        return self._instance.__getattribute__(name)

    def __setattr__(self, name: str, value: Any) -> None:
        self._instance.__setattr__(name, value)
