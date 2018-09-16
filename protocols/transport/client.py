import asyncio
from logging import Logger
from .base_transport import SerrializeProtocol, TCPConnection, TransportError, ConnectionState


class TCPClientConnection(TCPConnection):
    def __init__(self, logger: Logger):
        super().__init__(logger)
        self.__host: str = None
        self.__port: int = None
        self.__max_attempt: int = None

    async def connect(self, host: str, port: int, protocol: SerrializeProtocol,
                      max_attempt: int = -1) -> None:
        self._logger.info('Start connecting to %s:%d', host, port)

        self.__host = host
        self.__port = port
        self.__max_attempt = max_attempt
        ssl = (port == 443)
        attempt = 1
        while attempt <= max_attempt or max_attempt == -1:
            try:
                if self.state == ConnectionState.CLOSING:
                    self._logger.info('Connection is stopped because the transport is closed')
                    break

                if attempt != 1:
                    self._logger.info('Connection attempt %d', attempt)

                reader, writer = await asyncio.open_connection(host, port, ssl=ssl)
                self._logger.info('Connected to %s:%s', host, port)
                await self.run(protocol, reader, writer)
                break
            except ConnectionRefusedError as ex:
                self._logger.error('Error connecting to %s:%d, message: %s', host, port, ex)
                await asyncio.sleep(min(0.1 * attempt, 30))
                attempt += 1
        else:
            msg = 'Сould not connect to {}:{}'.format(host, port)
            self._logger.critical(msg)
            raise TransportError(msg)

    async def wait_reconnect_finished(self):
        while self.state not in [ConnectionState.RUNNING, ConnectionState.CLOSING]:
            await asyncio.sleep(0.1)

    async def on_lost_connection(self) -> None:
        assert self.__host is not None, 'Host not set'
        assert self.__port is not None, 'Port not set'
        assert self._protocol is not None, 'Protocol not set'
        assert self.__max_attempt is not None, 'Max attempt not set'
        await self.connect(self.__host, self.__port, self._protocol, self.__max_attempt)
