import re
import asyncio
from enum import Enum
from logging import Logger
from typing import List
from google.protobuf import message as gp_message


LOWER_CASE_FIRST_RE = re.compile('(.)([A-Z][a-z]+)')
LOWER_CASE_SECOND_RE = re.compile('([a-z0-9])([A-Z])')


class TransportError(RuntimeError):
    def __init__(self, message: str):
        super().__init__(message)


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
    UNINITIALIZED = 0
    RUNNING = 1
    LOST_CONNECTION = 2


class TCPConnection:
    def __init__(self, logger: Logger):
        self._logger = logger
        self._reader = None
        self._writer = None
        self._protocol = None
        self.__recv_loop_task = None
        self.__start_close = False
        self.__state: ConnectionState = ConnectionState.UNINITIALIZED

    @property
    def state(self) -> ConnectionState:
        return self.__state

    def __change_state(self, value: ConnectionState) -> None:
        self._logger.debug("Change state from %s to %s", self.__state.name, value.name)
        self.__state = value

    def __check_state(self) -> None:
        if self.__state == ConnectionState.LOST_CONNECTION:
            msg = 'TCPConnection has incorrect invalid status {}'.format(self.__state.name)
            raise LostConnection(TransportError(msg))

        if self.__state != ConnectionState.RUNNING:
            msg = 'TCPConnection has incorrect invalid status {}'.format(self.__state.name)
            raise TransportError(msg)

    async def send(self, message: gp_message) -> None:
        self.__check_state()

        try:
            return await self._protocol.send(self._writer, message)
        except ConnectionResetError as ex:
            await self.__on_lost_connection()
            self._reader = None
            raise LostConnection(ex)

    async def recv(self) -> gp_message:
        self.__check_state()

        try:
            return await self._protocol.recv(self._reader)
        except asyncio.IncompleteReadError as ex:
            await self.__on_lost_connection()
            self._writer.close()
            self._writer = None
            raise LostConnection(ex)
        except BrokenPipeError as ex:
            await self.__on_lost_connection()
            self._writer.close()
            self._writer = None
            raise LostConnection(ex)

    async def __on_lost_connection(self) -> None:
        if self.__state == ConnectionState.LOST_CONNECTION or self.__start_close:
            return

        self.__change_state(ConnectionState.LOST_CONNECTION)
        asyncio.ensure_future(self.__on_lost_connection_wrap())

    async def __on_lost_connection_wrap(self) -> None:
        if self.__recv_loop_task is not None:
            await asyncio.wait([self.__recv_loop_task])

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
        self.__change_state(ConnectionState.RUNNING)
        # TODO: process exception
        await self.on_connect()
        self.__recv_loop_task = asyncio.ensure_future(self.__recv_loop())
        return self.__recv_loop_task

    async def __recv_loop(self) -> None:
        handler_name = ''
        try:
            self._logger.info('Recv loop started')
            while self.__state == ConnectionState.RUNNING:
                message = await self.recv()

                handler_name = LOWER_CASE_FIRST_RE.sub(r'\1_\2', message.DESCRIPTOR.name)
                handler_name = 'on_' + LOWER_CASE_SECOND_RE.sub(r'\1_\2', handler_name).lower()
                handler = getattr(self, handler_name)
                await handler(message)
        except LostConnection as ex:
            msg = 'The receiving cycle is stopped by lost connection, origin exception (%s) %s'
            self._logger.error(msg, type(ex.exception), ex.exception)
        except AttributeError:
            self._logger.error('The receiving cycle is stopped, not found handler "{}"'
                               .format(handler_name))
            raise TransportError('Not found handler "{}"'.format(handler_name))
        except Exception as ex:
            self._logger.error('The receiving cycle is stopped by unknown exception (%s) %s',
                               type(ex), ex)
            raise ex
        finally:
            self._logger.info('Finished recv loop')

    async def close(self) -> None:
        # TODO: replace to state
        if self.__start_close:
            self._logger.info('Double close')
            return

        self._logger.debug('Connection close started')
        self.__start_close = True
        if self.__recv_loop_task is not None:
            self._reader.feed_eof()
            await asyncio.wait([self.__recv_loop_task])
            self.__recv_loop_task = None

        self._logger.info('Connection close finished')
