import re
import asyncio
from logging import Logger
from typing import List
from google.protobuf import message as gp_message


LOWER_CASE_FIRST_RE = re.compile('(.)([A-Z][a-z]+)')
LOWER_CASE_SECOND_RE = re.compile('([a-z0-9])([A-Z])')


class TransportError(RuntimeError):
    def __init__(self, message: str):
        RuntimeError.__init__(self, message)


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


class TCPConnection:
    def __init__(self, logger: Logger):
        self._logger = logger
        self._reader = None
        self._writer = None
        self._protocol = None
        self.__recv_loop_task = None
        self.__start_close = False

    async def send(self, message: gp_message) -> None:
        if self._writer is None:
            raise TransportError('Connection is not init')

        return await self._protocol.send(self._writer, message)

    async def recv(self) -> gp_message:
        if self._reader is None:
            raise TransportError('Connection is not init')

        return await self._protocol.recv(self._reader)

    async def on_connect(self) -> None:
        pass

    async def run(self, protocol: SerrializeProtocol,
                  reader: asyncio.streams.StreamReader,
                  writer: asyncio.streams.StreamWriter) -> asyncio.Task:
        self._protocol = protocol
        self._reader = reader
        self._writer = writer
        await self.on_connect()
        self.__recv_loop_task = asyncio.ensure_future(self.__recv_loop())
        return self.__recv_loop_task

    async def __recv_loop(self) -> None:
        handler_name = ''
        try:
            self._logger.info('Recv loop started')
            while True:
                message = await self.recv()

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
        except Exception as ex:
            self._logger.error('The receiving cycle is stopped by unknown exception %s', ex)
            raise ex
        finally:
            self._logger.info('Finished recv loop')

    async def close(self) -> None:
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
