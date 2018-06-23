from hashlib import md5
from struct import pack, unpack
from protocols.transport import ProtoTransportError, SerrializeProtocol


class HASerrializeProtocol(SerrializeProtocol):
    def __init__(self, protobuf_types, logger):
        self._logger = logger
        self._type_size = md5().digest_size
        self._types_map = {HASerrializeProtocol._hash(it.__name__) : it for it in protobuf_types}

    @staticmethod
    def _hash(message):
        return md5(message.encode('utf-8')).digest()

    async def send_protobuf(self, writer, message):
        message_bin = message.SerializeToString()
        message_name = message.DESCRIPTOR.name

        self._logger.debug('Send protobuf message "%s" (%d bytes)', message_name, len(message_bin))
        writer.write(pack('>I', len(message_bin) + self._type_size))
        writer.write(HASerrializeProtocol._hash(message_name))
        writer.write(message_bin)
        await writer.drain()

    async def recv_protobuf(self, reader):
        package_size_bin = await reader.readexactly(4)
        package_size = unpack('>I', package_size_bin)[0]
        package_bin = await reader.readexactly(package_size)
        proto_type = self._types_map.get(package_bin[:self._type_size], None)

        if proto_type is None:
            self._logger.debug('Recv unknown protobuf message (%d bytes)',
                               package_size - self._type_size)
            raise ProtoTransportError('Recv unknown protobuf message')

        message = proto_type()
        message.ParseFromString(package_bin[self._type_size:])
        self._logger.debug('Recv protobuf message "%s" (%d bytes)',
                          message.DESCRIPTOR.name, package_size - self._type_size)
        return message
