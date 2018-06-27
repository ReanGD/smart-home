import asyncio
from re import compile


LOWER_CASE_FIRST_RE = compile('(.)([A-Z][a-z]+)')
LOWER_CASE_SECOND_RE = compile('([a-z0-9])([A-Z])')


class ProtoTransportError(RuntimeError):
    def __init__(self, message):
        RuntimeError.__init__(self, message)


class SerrializeProtocol(object):
    async def send_protobuf(self, writer, message):
        raise Exception('Not implementation "send_protobuf"')

    async def recv_protobuf(self, reader):
        raise Exception('Not implementation "recv_protobuf"')


class ProtoConnection(object):
    def __init__(self, reader: asyncio.streams.StreamReader, writer: asyncio.streams.StreamWriter,
                 handler, protocol: SerrializeProtocol, logger, is_server: bool):
        self._logger = logger
        self._reader = reader
        self._writer = writer
        self._handler = handler
        self._protocol = protocol
        self._is_server = is_server
        self._recv_loop_task = None
        self._start_close = False

    async def send_protobuf(self, message):
        if self._writer is None:
            raise ProtoTransportError('Connection is not init')

        await self._protocol.send_protobuf(self._writer, message)

    async def recv_protobuf(self):
        if self._reader is None:
            raise ProtoTransportError('Connection is not init')

        return await self._protocol.recv_protobuf(self._reader)

    async def run_recv_loop(self):
        self._recv_loop_task = asyncio.ensure_future(self._recv_loop())
        return self._recv_loop_task

    async def _recv_loop(self):
        try:
            self._logger.info('recv loop started')
            while True:
                response = await self.recv_protobuf()

                handler_name = LOWER_CASE_FIRST_RE.sub(r'\1_\2', response.DESCRIPTOR.name)
                handler_name = 'on_' + LOWER_CASE_SECOND_RE.sub(r'\1_\2', handler_name).lower()
                handler = getattr(self._handler, handler_name)
                await handler(self, response)
        except asyncio.CancelledError:
            self._logger.debug('The receiving cycle is stopped by cancel')
        except asyncio.IncompleteReadError:
            self._logger.debug('The receiving cycle is stopped by eof')
        except Exception as e:
            self._logger.error('The receiving cycle is stopped by unknown exception %s', e)
            raise e
        finally:
            self._logger.info('Finished recv loop')

    async def close(self):
        if self._start_close:
            self._logger.info('Double close')
            return

        self._logger.debug('Connection close started')
        self._start_close = True
        if self._recv_loop_task is not None:
            self._reader.feed_eof()
            await asyncio.wait([self._recv_loop_task])
            self._recv_loop_task = None
            self._reader = None
            self._handler = None
            self._protocol = None

        if self._writer is not None:
            self._writer.close()
            self._writer = None

        self._logger.info('Connection close finished')


async def create_client(host: str, port: int, handler_factory, protocol: SerrializeProtocol, logger,
                        max_attempt: int=5) -> ProtoConnection:
    logger.info('Start connecting to %s:%d', host, port)

    ssl = (port == 443)
    connection = None
    handler = handler_factory()
    for attempt in range(max_attempt):
        try:
            if attempt != 0:
                logger.info('Connection attempt %d', attempt + 1)

            reader, writer = await asyncio.open_connection(host, port, ssl=ssl)
            connection = ProtoConnection(reader, writer, handler, protocol, logger, False)
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


class ProtoServer(object):
    def __init__(self, server_coro, logger):
        self._connections = set()
        self._logger = logger
        self._server_task = asyncio.ensure_future(server_coro)

    def add_connection(self, connection: ProtoConnection):
        self._connections.add(connection)

    def remove_connection(self, connection: ProtoConnection):
        self._connections.remove(connection)

    async def send_protobuf_to_all(self, message):
        tasks = [connection.send_protobuf(message) for connection in self._connections]
        await asyncio.gather(*tasks)

    async def close(self):
        self._logger.debug('Server close started')
        tasks = [connection.close() for connection in self._connections]
        await asyncio.gather(*tasks)
        self._connections.clear()

        server = self._server_task.result()
        server.close()
        await server.wait_closed()
        self._logger.info('Sever close finished')


class ServerStreamReaderProtocol(asyncio.streams.FlowControlMixin):
    def __init__(self, server: ProtoServer, handler_factory, protocol, logger):
        super().__init__()
        self._server = server
        self._handler = handler_factory()
        self._protocol = protocol
        self._logger = logger

        self._stream_reader = asyncio.StreamReader()
        self._connection = None
        self._over_ssl = False

    def connection_made(self, transport):
        self._logger.info('Accept connect')
        self._stream_reader.set_transport(transport)
        self._over_ssl = transport.get_extra_info('sslcontext') is not None
        stream_writer = asyncio.StreamWriter(transport, self, self._stream_reader, self._loop)

        self._connection = ProtoConnection(self._stream_reader, stream_writer, self._handler,
                                           self._protocol, self._logger, True)
        self._server.add_connection(self._connection)
        # TODO: remove task?
        self._loop.create_task(self.on_accept())

    async def on_accept(self):
        try:
            recv_loop = await self._connection.run_recv_loop()
            asyncio.wait(recv_loop)
        except Exception as e:
            self._logger.error('unknown exception: %s', e)
        finally:
            self._logger.info('Connect was closed')

    def connection_lost(self, exc):
        self._logger.debug('connection_lost')
        if self._stream_reader is not None:
            if exc is None:
                self._stream_reader.feed_eof()
            else:
                self._stream_reader.set_exception(exc)
        super().connection_lost(exc)
        self._stream_reader = None

    def data_received(self, data):
        self._stream_reader.feed_data(data)

    def eof_received(self):
        self._server.remove_connection(self._connection)
        asyncio.ensure_future(self._connection.close())
        self._stream_reader = None

        if self._over_ssl:
            # Prevent a warning in SSLProtocol.eof_received:
            # "returning true from eof_received()
            # has no effect when using ssl"
            return False
        return True


async def create_server(host: str, port: int, handler_factory, protocol: SerrializeProtocol,
                        logger) -> ProtoServer:
    logger.info('Start server on %s:%d', host, port)
    server = None

    def factory():
        return ServerStreamReaderProtocol(server, handler_factory, protocol, logger)

    server = ProtoServer(asyncio.get_event_loop().create_server(factory, host, port), logger)
    return server
