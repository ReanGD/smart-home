import asyncio


class BaseTransportError(RuntimeError):
    def __init__(self, message):
        RuntimeError.__init__(self, message)


class ProtoConnection(object):
    def __init__(self, reader, writer, handler, protobuf_types, logger):
        self.logger = logger
        self._reader = reader
        self._writer = writer
        self._handler = handler
        self._protobuf_types = protobuf_types
        self._recv_loop_task = None

    async def send_protobuf(self, message):
        data_bin = message.SerializeToString()
        data_len = len(data_bin)
        self.logger.debug('Send protobuf message "%s" (%d bytes)',
                          message.DESCRIPTOR.name, data_len)
        self._writer.write(hex(data_len)[2:].encode("utf-8"))
        self._writer.write(b'\r\n')
        self._writer.write(data_bin)
        await self._writer.drain()

    async def recv_protobuf(self):
        size_bin = await self._reader.readuntil(b'\r\n')
        size_int = int(b'0x' + size_bin[:-2], 0)
        data_bin = await self._reader.readexactly(size_int)

        saved_exception = None
        for proto_type in self._protobuf_types:
            message = proto_type()
            try:
                message.ParseFromString(data_bin)
                self.logger.debug('Recv protobuf message "%s" (%d bytes)',
                                  message.DESCRIPTOR.name, size_int)
                return message
            except Exception as exc:
                saved_exception = exc

        self.logger.debug('Recv unknown protobuf message (%d bytes)',
                          size_int)
        raise saved_exception

    async def run_recv_loop(self):
        self._recv_loop_task = asyncio.ensure_future(self._recv_loop())
        return self._recv_loop_task

    async def _recv_loop(self):
        try:
            self.logger.info('recv loop started')
            while True:
                response = await self.recv_protobuf()
                func = getattr(self._handler, 'on_' + response.DESCRIPTOR.name)
                await func(self._handler, self, response)
        except asyncio.futures.CancelledError:
            pass
        finally:
            self._recv_loop_task = None
            self.logger.info('recv loop finished')

    async def close(self):
        self.logger.info('Connection close started')
        if self._recv_loop_task is not None:
            task = self._recv_loop_task
            task.cancel()
            await asyncio.wait([task])
            self._recv_loop_task = None

        if self._writer is not None:
            self._writer.close()
            self._writer = None

        self._reader = None
        self._handler = None
        self.logger.info('Connection close finished')


class ProtoServer(object):
    def __init__(self, task):
        self._connections = set()
        self._server_task = asyncio.ensure_future(task)

    def add_connection(self, connection: ProtoConnection):
        self._connections.add(connection)


async def create_client(host: str, port: int, handler_class, protobuf_types, logger,
                        max_attempt: int=5) -> ProtoConnection:
    logger.info('Start connecting to %s:%d', host, port)

    ssl = (port == 443)
    connection = None
    handler = handler_class()
    for attempt in range(max_attempt):
        try:
            if attempt != 0:
                logger.info('Connection attempt %d', attempt + 1)

            reader, writer = await asyncio.open_connection(host, port, ssl=ssl)
            connection = ProtoConnection(reader, writer, handler, protobuf_types, logger)
            logger.info('Connected to %s:%s', host, port)
            break
        except ConnectionRefusedError as ex:
            if attempt + 1 == max_attempt:
                logger.critical('Сould not connect to %s:%d, message: %s', host, port)
                raise
            else:
                logger.error('Error connecting to %s:%d, message: %s', host, port, ex)
                await asyncio.sleep(0.5)

    await handler.on_connect()
    await connection.run_recv_loop()

    return connection


async def create_server(host: str, port: int, handler_class, protobuf_types, logger) -> ProtoServer:
    logger.info('Start server on %s:%d', host, port)
    server = None

    async def on_accept(reader, writer):
        logger.info('Accept connect')
        connection = ProtoConnection(reader, writer, handler_class, protobuf_types, logger)
        server.add_connection(connection)
        recv_loop = await connection.run_recv_loop()
        asyncio.wait(recv_loop)

    server = ProtoServer(asyncio.start_server(on_accept, host, port))
    return server
