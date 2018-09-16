import re
import asyncio
from enum import Enum, auto
from logging import Logger
from typing import List
from google.protobuf import message as gp_message


LOWER_CASE_FIRST_RE = re.compile('(.)([A-Z][a-z]+)')
LOWER_CASE_SECOND_RE = re.compile('([a-z0-9])([A-Z])')


class TransportError(RuntimeError):
    def __init__(self, message: str):
        super().__init__(message)


class StateError(TransportError):
    pass


class LostConnection(RuntimeError):
    def __init__(self, ex: Exception):
        super().__init__('Lost connection')
        self.exception = ex


class SerrializeProtocol:
    def __init__(self, protobuf_types: List[object], logger):
        self._logger = logger
        self._protobuf_types = protobuf_types

    @property
    def protobuf_types(self) -> List[object]:
        return self._protobuf_types

    @protobuf_types.setter
    def protobuf_types(self, value: List[object]):
        self._protobuf_types = value

    async def send(self, _writer: asyncio.streams.StreamWriter, _message: gp_message) -> None:
        raise TransportError('Not implementation "send"')

    async def recv(self, _reader: asyncio.streams.StreamReader) -> gp_message:
        raise TransportError('Not implementation "recv"')


class ConnectionState(Enum):
    UNINITIALIZED = auto()
    INITIALIZATION = auto()
    RUNNING = auto()
    LOST_CONNECTION = auto()
    CLOSING = auto()


class TCPConnection:
    def __init__(self, logger: Logger):
        self._logger = logger
        self._reader: asyncio.streams.StreamReader = None
        self._writer: asyncio.streams.StreamWriter = None
        self.__reader_lock = asyncio.Lock()
        self.__writer_lock = asyncio.Lock()
        self._protocol = None
        self.__recv_loop_task = None
        self.__state = ConnectionState.UNINITIALIZED

    @property
    def state(self) -> ConnectionState:
        return self.__state

    def __change_state(self, value: ConnectionState) -> None:
        self._logger.debug("Change state from %s to %s", self.__state.name, value.name)
        self.__state = value

    async def send(self, message: gp_message) -> None:
        try:
            await self.__writer_lock.acquire()

            if self.__state == ConnectionState.LOST_CONNECTION:
                raise LostConnection(StateError('Failed to send message, lost connection'))

            if self.__state == ConnectionState.CLOSING:
                raise StateError('Failed to send message, connection closed')

            if self.__state not in [ConnectionState.INITIALIZATION, ConnectionState.RUNNING]:
                msg = 'Failed to send message, incorrect state: {}'.format(self.__state.name)
                raise StateError(msg)

            try:
                return await self._protocol.send(self._writer, message)
            except ConnectionResetError as ex:
                asyncio.ensure_future(self.__on_lost_connection())
                raise LostConnection(ex)
        finally:
            self.__writer_lock.release()

    async def recv(self) -> gp_message:
        try:
            await self.__reader_lock.acquire()

            if self.__state == ConnectionState.LOST_CONNECTION:
                raise LostConnection(StateError('Stopped receiving, lost connection'))

            if self.__state == ConnectionState.CLOSING:
                raise StateError('Stopped receiving, connection closed')

            if self.__state not in [ConnectionState.INITIALIZATION, ConnectionState.RUNNING]:
                msg = 'Stopped receiving, incorrect state: {}'.format(self.__state.name)
                raise StateError(msg)

            try:
                return await self._protocol.recv(self._reader)
            except (asyncio.IncompleteReadError, BrokenPipeError) as ex:
                self._logger.error('Stopped receiving, lost connection: <%s> %s', type(ex), ex)
                asyncio.ensure_future(self.__on_lost_connection())
                raise LostConnection(ex)
            except TransportError:
                raise
            except Exception as ex:
                self._logger.error('Stopped receiving, unknown exception: <%s> %s', type(ex), ex)
                raise
        finally:
            self.__reader_lock.release()

    async def __on_lost_connection(self) -> None:
        if self.__state not in [ConnectionState.LOST_CONNECTION, ConnectionState.CLOSING]:
            await self.__close(ConnectionState.LOST_CONNECTION)
            await self.on_lost_connection()

    async def on_lost_connection(self) -> None:
        pass

    async def on_connect(self) -> None:
        pass

    async def run(self, protocol: SerrializeProtocol,
                  reader: asyncio.streams.StreamReader,
                  writer: asyncio.streams.StreamWriter) -> asyncio.Task:
        self._protocol = protocol
        self._reader = reader
        self._writer = writer
        self.__change_state(ConnectionState.INITIALIZATION)

        try:
            await self.on_connect()
        except LostConnection as ex:
            ex = ex.exception
            self._logger.error(('Handler "on_connect" is stopped by lost connection, '
                                'origin exception: <%s> %s'), type(ex), ex)
            asyncio.ensure_future(self.__on_lost_connection())
            raise
        except StateError as ex:
            self._logger.error('Handler "on_connect" is stopped by state error: %s', ex)
            # TODO: fix me
            return None
        except Exception as ex:
            self._logger.error('Handler "on_connect" is stopped by unknown exception: <%s> %s',
                               type(ex), ex)
            raise

        self.__recv_loop_task = asyncio.ensure_future(self.__recv_loop())
        return self.__recv_loop_task

    async def __recv_loop(self) -> None:
        try:
            self._logger.info('Recv loop started')
            handler_name = ''
            message = None
            self.__change_state(ConnectionState.RUNNING)
            while True:
                if self.__state != ConnectionState.RUNNING:
                    self._logger.error('The receiving cycle is stopped, incorrect state: %s',
                                       self.__state.name)
                    break

                try:
                    message = await self.recv()
                except LostConnection as ex:
                    ex = ex.exception
                    self._logger.error(('The receiving cycle is stopped by lost connection, '
                                        'origin exception: <%s> %s'), type(ex), ex)
                    break
                except StateError as ex:
                    self._logger.error('The receiving cycle is stopped by state error: %s ', ex)
                    break
                except TransportError:
                    pass
                except Exception as ex:
                    msg = 'The receiving cycle is stopped by unknown exception in recv: <%s> %s'
                    self._logger.error(msg, type(ex), ex)
                    raise

                try:
                    handler_name = LOWER_CASE_FIRST_RE.sub(r'\1_\2', message.DESCRIPTOR.name)
                    handler_name = 'on_' + LOWER_CASE_SECOND_RE.sub(r'\1_\2', handler_name).lower()
                    handler = getattr(self, handler_name)
                    await handler(message)
                except AttributeError:
                    self._logger.error('The receiving cycle is stopped, not found handler "{}"'
                                       .format(handler_name))
                    raise TransportError('Not found handler "{}"'.format(handler_name))
                except Exception as ex:
                    self._logger.error(('The receiving cycle is stopped by unknown exception '
                                        'in handler (%s): <%s> %s'), handler_name, type(ex), ex)
                    raise
        finally:
            self._logger.info('Finished recv loop')

    async def __close(self, new_state: ConnectionState):
        self.__change_state(new_state)

        if self._writer is not None:
            try:
                await self.__writer_lock.acquire()
                self._writer.close()
                self._writer = None
            finally:
                self.__writer_lock.release()

        if self._reader is not None:
            try:
                self._reader.feed_eof()
                await self.__reader_lock.acquire()
                self._reader = None
            finally:
                self.__reader_lock.release()

        if self.__recv_loop_task is not None:
            await asyncio.wait([self.__recv_loop_task])
            self.__recv_loop_task = None

    async def close(self) -> None:
        if self.__state == ConnectionState.CLOSING:
            self._logger.warning('Double close')
        elif self.__state == ConnectionState.LOST_CONNECTION:
            self.__change_state(ConnectionState.CLOSING)
            self._logger.info('Close after lost connection')
        else:
            await self.__close(ConnectionState.CLOSING)
            self._logger.info('Connection close finished')
