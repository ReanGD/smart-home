import asyncio
from logging import Logger
from typing import Callable
from google.protobuf import message as gp_message
from .base_transport import SerrializeProtocol, TCPConnection


class TCPServerConnection(TCPConnection):
    pass


class TCPServerProtocol(asyncio.streams.FlowControlMixin):
    def __init__(self,
                 server: 'TCPServer',
                 handler_factory: Callable[[Logger], TCPServerConnection],
                 protocol: SerrializeProtocol,
                 logger: Logger):
        super().__init__()
        self._server = server
        self._protocol = protocol
        self._logger = logger

        self._stream_reader = asyncio.StreamReader()
        self._connection = handler_factory(logger)
        self._over_ssl = False

    def connection_made(self, transport) -> None:
        self._loop.create_task(self.on_accept(transport))

    async def on_accept(self, transport) -> None:
        self._logger.info('Accept connect')
        try:
            self._stream_reader.set_transport(transport)
            self._over_ssl = transport.get_extra_info('sslcontext') is not None
            stream_writer = asyncio.StreamWriter(transport, self, self._stream_reader, self._loop)
            task = await self._connection.run(self._protocol, self._stream_reader, stream_writer)
            self._server.add_connection(self._connection)
            await task
        except Exception as ex:
            self._logger.error('Unknown exception: %s', ex)
            raise ex
        finally:
            self._logger.info('Connect was closed')

    def connection_lost(self, exc: Exception) -> None:
        self._logger.debug('Connection lost')
        if self._stream_reader is not None:
            if exc is None:
                self._stream_reader.feed_eof()
            else:
                self._stream_reader.set_exception(exc)
        super().connection_lost(exc)
        self._stream_reader = None

    def data_received(self, data: bytes) -> None:
        self._stream_reader.feed_data(data)

    def eof_received(self) -> bool:
        self._server.remove_connection(self._connection)
        asyncio.ensure_future(self._connection.close())
        self._stream_reader = None

        if self._over_ssl:
            # Prevent a warning in SSLProtocol.eof_received:
            # "returning true from eof_received()
            # has no effect when using ssl"
            return False
        return True


class TCPServer:
    def __init__(self, logger: Logger):
        self._connections = set()
        self._logger = logger
        self._server_task = None

    def add_connection(self, connection: TCPServerConnection) -> None:
        self._connections.add(connection)

    def remove_connection(self, connection: TCPServerConnection) -> None:
        self._connections.remove(connection)

    async def send_to_all(self, message: gp_message) -> None:
        tasks = [connection.send(message) for connection in self._connections]
        await asyncio.gather(*tasks)

    async def run(self, host: str, port: int,
                  handler_factory: Callable[[Logger], TCPServerConnection],
                  protocol: SerrializeProtocol) -> 'TCPServer':
        self._logger.info('Start server on %s:%d', host, port)

        def factory() -> TCPServerProtocol:
            return TCPServerProtocol(self, handler_factory, protocol, self._logger)

        server_coro = asyncio.get_event_loop().create_server(factory, host, port)
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
