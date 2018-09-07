import asyncio
from .base_transport import SerrializeProtocol, TCPConnection, TransportError


class TCPClientConnection(TCPConnection):
    async def connect(self, host: str, port: int, protocol: SerrializeProtocol,
                      max_attempt: int = 5) -> None:
        self._logger.info('Start connecting to %s:%d', host, port)

        ssl = (port == 443)
        for attempt in range(max_attempt):
            try:
                if attempt != 0:
                    self._logger.info('Connection attempt %d', attempt + 1)

                reader, writer = await asyncio.open_connection(host, port, ssl=ssl)
                self._logger.info('Connected to %s:%s', host, port)
                await self.run(protocol, reader, writer)
                break
            except ConnectionRefusedError as ex:
                self._logger.error('Error connecting to %s:%d, message: %s', host, port, ex)
                await asyncio.sleep(0.5)
        else:
            msg = 'Сould not connect to {}:{}'.format(host, port)
            self._logger.critical(msg)
            raise TransportError(msg)
