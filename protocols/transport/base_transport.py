import asyncio


class ProtoTransportError(RuntimeError):
    def __init__(self, message):
        RuntimeError.__init__(self, message)


class SerrializeProtocol(object):
    async def send_protobuf(self, writer, message):
        raise Exception('Not implementation "send_protobuf"')

    async def recv_protobuf(self, reader):
        raise Exception('Not implementation "recv_protobuf"')


class ProtoConnection(object):
    def __init__(self, reader, writer, handler, protocol: SerrializeProtocol, logger):
        self._logger = logger
        self._reader = reader
        self._writer = writer
        self._handler = handler
        self._protocol = protocol
        self._recv_loop_task = None

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
                method = getattr(self._handler, 'on_' + response.DESCRIPTOR.name)
                await method(self, response)
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
        self._logger.info('Connection close started')
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
            connection = ProtoConnection(reader, writer, handler, protocol, logger)
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
    def __init__(self, task):
        self._connections = set()
        self._server_task = asyncio.ensure_future(task)

    def add_connection(self, connection: ProtoConnection):
        self._connections.add(connection)

    async def close(self):
        # TODO close all
        for connection in self._connections:
            await connection.close()


async def create_server(host: str, port: int, handler_factory, protocol: SerrializeProtocol,
                        logger) -> ProtoServer:
    logger.info('Start server on %s:%d', host, port)
    server = None

    async def on_accept(reader, writer):
        logger.info('Accept connect')
        connection = ProtoConnection(reader, writer, handler_factory(), protocol, logger)
        server.add_connection(connection)
        try:
            recv_loop = await connection.run_recv_loop()
            asyncio.wait(recv_loop)
        except Exception as e:
            logger.error('unknown exception 2: %s', e)
        finally:
            logger.info('Connect was closed')

    server = ProtoServer(asyncio.start_server(on_accept, host, port))
    return server
