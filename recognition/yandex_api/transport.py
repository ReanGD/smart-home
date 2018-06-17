from asyncio import open_connection, sleep
from logging import getLogger


logger = getLogger('yanader_transport')


class YandexTransportError(RuntimeError):
    def __init__(self, message):
        RuntimeError.__init__(self, message)


class Transport(object):
    def __init__(self):
        self._reader = None
        self._writer = None

    async def connect(self, host, port):
        logger.info('Start connecting to %s:%d', host, port)

        ssl = (port == 443)
        last_ex = None
        for attempt in range(5):
            try:
                if attempt != 0:
                    logger.info('Connection attempt %d', attempt+1)

                self._reader, self._writer = await open_connection(host, port, ssl=ssl)
                logger.info('Connected to %s:%s', host, port)
                return
            except ConnectionRefusedError as ex:
                last_ex = ex
                logger.error('Error connecting to %s:%d, message: %s', host, port, ex)
                await sleep(0.5)

        logger.critical('Сould not connect to %s:%d, message: %s', host, port)
        raise last_ex

    async def upgrade_connection(self, app, host, port):
        request = ('GET /asr_partial_checked HTTP/1.1\r\n'
                   'User-Agent: {app}\r\n'
                   'Host: {host}:{port}\r\n'
                   'Upgrade: dictation\r\n\r\n'
                   ).format(app=app, host=host, port=port).encode("utf-8")
        logger.debug('Start of connection upgrade')
        self._writer.write(request)
        await self._writer.drain()

        answer = await self._reader.readuntil(b'\r\n\r\n')
        if not answer.decode('utf-8').startswith('HTTP/1.1 101 Switching Protocols'):
            raise YandexTransportError('Unable to upgrade connection')

    async def send_protobuf(self, protobuf):
        data_bin = protobuf.SerializeToString()
        data_len = len(data_bin)
        logger.debug('Send protobuf package (%d bytes)', data_len)
        self._writer.write(hex(data_len)[2:].encode("utf-8"))
        self._writer.write(b'\r\n')
        self._writer.write(data_bin)
        await self._writer.drain()

    async def recv_protobuf(self, *protobuf_types):
        size_bin = await self._reader.readuntil(b'\r\n')
        size_int = int(b'0x' + size_bin[:-2], 0)
        data_bin = await self._reader.readexactly(size_int)

        logger.debug('Recv protobuf package (%d bytes)', size_int)
        saved_exception = None
        for proto_type in protobuf_types:
            response = proto_type()
            try:
                response.ParseFromString(data_bin)
                return response
            except Exception as exc:
                saved_exception = exc

        raise saved_exception

    def close(self):
        self._writer.close()
        self._writer = None
        self._reader = None
        logger.info('Connection closed')
