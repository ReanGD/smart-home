import asyncio
from logging import Logger
from .base_transport import SerrializeProtocol, TCPConnection, TransportError, ConnectionState
from .config import TransportConfig


class TCPClientConnection(TCPConnection):
    def __init__(self, logger: Logger, config: TransportConfig):
        super().__init__(logger)
        self._config = config
        self._max_attempt: int = None

    async def __connect(self, protocol: SerrializeProtocol) -> None:
        self._logger.info('Start connecting to %s', self._config)

        host = self._config.host
        port = self._config.port
        max_attempt = self._max_attempt

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

    async def connect(self, protocol: SerrializeProtocol, max_attempt: int = -1) -> None:
        self._max_attempt = max_attempt
        self._change_state(ConnectionState.UNINITIALIZED)
        await self.__connect(protocol)

    async def wait_reconnect_finished(self):
        while self.state not in [ConnectionState.RUNNING, ConnectionState.CLOSING]:
            await asyncio.sleep(0.01)

    async def on_lost_connection(self) -> None:
        assert self._protocol is not None, 'Protocol not set'
        assert self._max_attempt is not None, 'Max attempt not set'
        await self.__connect(self._protocol)
