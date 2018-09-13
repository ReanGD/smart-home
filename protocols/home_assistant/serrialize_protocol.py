import asyncio
from hashlib import md5
from typing import List
from struct import pack, unpack
from google.protobuf import message as gp_message
from protocols.transport import TransportError, SerrializeProtocol


class HASerrializeProtocol(SerrializeProtocol):
    def __init__(self, protobuf_types: List[object], logger):
        super().__init__(protobuf_types, logger)
        self._type_size = md5().digest_size
        self._types_map = {HASerrializeProtocol._hash(it.__name__) : it for it in protobuf_types}

    @staticmethod
    def _hash(message: str) -> bytes:
        return md5(message.encode('utf-8')).digest()

    async def send(self, writer: asyncio.streams.StreamWriter, message: gp_message) -> None:
        message_bin = message.SerializeToString()
        message_len = len(message_bin)
        message_name = message.DESCRIPTOR.name
        try:
            self._logger.debug('Send protobuf message "%s" (%d bytes)',
                               message_name, message_len)
            writer.write(pack('>I', message_len + self._type_size))
            writer.write(HASerrializeProtocol._hash(message_name))
            writer.write(message_bin)
            await writer.drain()
        except ConnectionResetError:
            msg = 'Send protobuf message "%s" (%d bytes) finished with error: Connection lost'
            self._logger.error(msg, message_name, message_len)
            raise
        except Exception as ex:
            msg = 'Send protobuf message "%s" (%d bytes) finished with error: <%s> %s'
            self._logger.error(msg, message_name, message_len, type(ex), ex)
            raise

    async def recv(self, reader: asyncio.streams.StreamReader) -> gp_message:
        package_size_bin = await reader.readexactly(4)
        package_size = unpack('>I', package_size_bin)[0]
        package_bin = await reader.readexactly(package_size)
        proto_type = self._types_map.get(package_bin[:self._type_size], None)

        if proto_type is None:
            self._logger.debug('Recv unknown protobuf message (%d bytes)',
                               package_size - self._type_size)
            raise TransportError('Recv unknown protobuf message')

        message = proto_type()
        message.ParseFromString(package_bin[self._type_size:])
        self._logger.debug('Recv protobuf message "%s" (%d bytes)',
                           message.DESCRIPTOR.name, package_size - self._type_size)
        return message
