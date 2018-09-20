import asyncio
from logging import Logger
from typing import Callable
from google.protobuf import message as gp_message
from .base_transport import SerrializeProtocol, TCPConnection


class TCPServerConnection(TCPConnection):
    async def on_lost_connection(self) -> None:
        pass


class TCPServer:
    def __init__(self, logger: Logger):
        self._connections = set()
        self._logger = logger
        self._server_task = None
        self._handler_factory: Callable[[Logger], TCPServerConnection] = None
        self._protocol: SerrializeProtocol = None

    async def send_to_all(self, message: gp_message) -> None:
        tasks = [connection.send(message) for connection in self._connections]
        await asyncio.gather(*tasks)

    def connection_count(self) -> int:
        return len(self._connections)

    async def __handle_connection(self,
                                  reader: asyncio.streams.StreamReader,
                                  writer: asyncio.streams.StreamWriter) -> None:
        # pylint: disable=broad-except
        self._logger.info('Accept connect')
        try:
            connection = self._handler_factory(self._logger)
            task = await connection.run(self._protocol, reader, writer)
            self._connections.add(connection)
            await task
            self._connections.remove(connection)
            self._logger.info('Connect was closed')
        except Exception as ex:
            self._logger.info('Connect was closed, with message: %s', ex)

    async def run(self, host: str, port: int,
                  handler_factory: Callable[[Logger], TCPServerConnection],
                  protocol: SerrializeProtocol) -> 'TCPServer':
        self._logger.info('Start server on %s:%d', host, port)
        self._handler_factory = handler_factory
        self._protocol = protocol
        server_coro = asyncio.start_server(self.__handle_connection, host, port)
        self._server_task = asyncio.ensure_future(server_coro)

        return self

    async def close(self) -> None:
        self._logger.debug('Server close started')
        tasks = [connection.close() for connection in self._connections]
        await asyncio.gather(*tasks)
        self._connections.clear()

        server = self._server_task.result()
        server.close()
        await server.wait_closed()
        self._logger.info('Sever close finished')
