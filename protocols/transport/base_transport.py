import re
import asyncio


LOWER_CASE_FIRST_RE = re.compile('(.)([A-Z][a-z]+)')
LOWER_CASE_SECOND_RE = re.compile('([a-z0-9])([A-Z])')


class TransportError(RuntimeError):
    def __init__(self, message):
        RuntimeError.__init__(self, message)


class SerrializeProtocol(object):
    def __init__(self, protobuf_types, logger):
        self._logger = logger
        self._protobuf_types = protobuf_types

    @property
    def protobuf_types(self):
        return self._protobuf_types

    @protobuf_types.setter
    def protobuf_types(self, value):
        self._protobuf_types = value

    async def send_protobuf(self, writer, message):
        raise TransportError('Not implementation "send_protobuf"')

    async def recv_protobuf(self, reader):
        raise TransportError('Not implementation "recv_protobuf"')


class ProtoConnection(object):
    def __init__(self, logger):
        self._logger = logger
        self._reader = None
        self._writer = None
        self._protocol = None
        self.__recv_loop_task = None
        self.__start_close = False

    async def send_protobuf(self, message):
        if self._writer is None:
            raise TransportError('Connection is not init')

        return await self._protocol.send_protobuf(self._writer, message)

    async def recv_protobuf(self):
        if self._reader is None:
            raise TransportError('Connection is not init')

        return await self._protocol.recv_protobuf(self._reader)

    async def on_connect(self):
        pass

    async def run(self, protocol: SerrializeProtocol,
                  reader: asyncio.streams.StreamReader,
                  writer: asyncio.streams.StreamWriter):
        self._protocol = protocol
        self._reader = reader
        self._writer = writer
        await self.on_connect()
        self.__recv_loop_task = asyncio.ensure_future(self.__recv_loop())
        return self.__recv_loop_task

    async def __recv_loop(self):
        handler_name = ''
        try:
            self._logger.info('Recv loop started')
            while True:
                message = await self.recv_protobuf()

                handler_name = LOWER_CASE_FIRST_RE.sub(r'\1_\2', message.DESCRIPTOR.name)
                handler_name = 'on_' + LOWER_CASE_SECOND_RE.sub(r'\1_\2', handler_name).lower()
                handler = getattr(self, handler_name)
                await handler(message)
        except asyncio.CancelledError:
            self._logger.debug('The receiving cycle is stopped by cancel')
        except asyncio.IncompleteReadError:
            self._logger.debug('The receiving cycle is stopped by eof')
        except AttributeError:
            self._logger.error('The receiving cycle is stopped, not found handler "{}"'
                               .format(handler_name))
            raise TransportError('Not found handler "{}"'.format(handler_name))
        except Exception as e:
            self._logger.error('The receiving cycle is stopped by unknown exception %s', e)
            raise e
        finally:
            self._logger.info('Finished recv loop')

    async def connect(self, host: str, port: int, protocol: SerrializeProtocol,
                      max_attempt: int = 5):
        self._logger.info('Start connecting to %s:%d', host, port)

        ssl = (port == 443)
        for attempt in range(max_attempt):
            try:
                if attempt != 0:
                    self._logger.info('Connection attempt %d', attempt + 1)

                reader, writer = await asyncio.open_connection(host, port, ssl=ssl)
                self._logger.info('Connected to %s:%s', host, port)
                await self.run(protocol, reader, writer)
                return
            except ConnectionRefusedError as ex:
                self._logger.error('Error connecting to %s:%d, message: %s', host, port, ex)
                await asyncio.sleep(0.5)
        else:
            msg = 'Сould not connect to {}:{}'.format(host, port)
            self._logger.critical(msg)
            raise TransportError(msg)

    async def close(self):
        if self.__start_close:
            self._logger.info('Double close')
            return

        self._logger.debug('Connection close started')
        self.__start_close = True
        if self.__recv_loop_task is not None:
            self._reader.feed_eof()
            await asyncio.wait([self.__recv_loop_task])
            self.__recv_loop_task = None
            self._reader = None
            self._protocol = None

        if self._writer is not None:
            self._writer.close()
            self._writer = None

        self._logger.info('Connection close finished')


class ServerStreamReaderProtocol(asyncio.streams.FlowControlMixin):
    def __init__(self, server: 'ProtoServer', handler_factory, protocol, logger):
        super().__init__()
        self._server = server
        self._protocol = protocol
        self._logger = logger

        self._stream_reader = asyncio.StreamReader()
        self._connection = handler_factory(logger)
        self._over_ssl = False

    def connection_made(self, transport):
        self._loop.create_task(self.on_accept(transport))

    async def on_accept(self, transport):
        self._logger.info('Accept connect')
        try:
            self._stream_reader.set_transport(transport)
            self._over_ssl = transport.get_extra_info('sslcontext') is not None
            stream_writer = asyncio.StreamWriter(transport, self, self._stream_reader, self._loop)
            task = await self._connection.run(self._protocol, self._stream_reader, stream_writer)
            self._server.add_connection(self._connection)
            await task
        except Exception as e:
            self._logger.error('Unknown exception: %s', e)
            raise e
        finally:
            self._logger.info('Connect was closed')

    def connection_lost(self, exc):
        self._logger.debug('Connection lost')
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


class ProtoServer(object):
    def __init__(self, logger):
        self._connections = set()
        self._logger = logger
        self._server_task = None

    def add_connection(self, connection: ProtoConnection):
        self._connections.add(connection)

    def remove_connection(self, connection: ProtoConnection):
        self._connections.remove(connection)

    async def send_protobuf_to_all(self, message):
        tasks = [connection.send_protobuf(message) for connection in self._connections]
        await asyncio.gather(*tasks)

    async def run(self, host: str, port: int, handler_factory, protocol: SerrializeProtocol):
        self._logger.info('Start server on %s:%d', host, port)

        def factory():
            return ServerStreamReaderProtocol(self, handler_factory, protocol, self._logger)

        server_coro = asyncio.get_event_loop().create_server(factory, host, port)
        self._server_task = asyncio.ensure_future(server_coro)

        return self

    async def close(self):
        self._logger.debug('Server close started')
        tasks = [connection.close() for connection in self._connections]
        await asyncio.gather(*tasks)
        self._connections.clear()

        server = self._server_task.result()
        server.close()
        await server.wait_closed()
        self._logger.info('Sever close finished')
