import asyncio
from .basic_pb2 import ConnectionResponse
from .voiceproxy_pb2 import AdvancedASROptions, ConnectionRequest, AddData
from protocols.transport import TransportError, SerrializeProtocol, ProtoConnectionHandler, ProtoConnection


class YandexSerrializeProtocol(SerrializeProtocol):
    def __init__(self, protobuf_types, logger):
        super().__init__(protobuf_types, logger)

    async def send_protobuf(self, writer, message):
        message_bin = message.SerializeToString()
        message_len = len(message_bin)
        message_name = message.DESCRIPTOR.name

        self._logger.debug('Send protobuf message "%s" (%d bytes)', message_name, message_len)
        writer.write(hex(message_len)[2:].encode('utf-8'))
        writer.write(b'\r\n')
        writer.write(message_bin)
        await writer.drain()

    async def recv_protobuf(self, reader):
        package_size_bin = await reader.readuntil(b'\r\n')
        package_size = int(b'0x' + package_size_bin[:-2], 0)
        package_bin = await reader.readexactly(package_size)

        for proto_type in self._protobuf_types:
            message = proto_type()
            try:
                message.ParseFromString(package_bin)
                self._logger.debug('Recv protobuf message "%s" (%d bytes)', message.DESCRIPTOR.name, package_size)
                return message
            except Exception:
                pass

        self._logger.debug('Recv unknown protobuf message (%d bytes)', package_size)
        raise TransportError('Recv unknown protobuf message')


class YandexProtoConnectionHandler(ProtoConnectionHandler):
    def __init__(self, app, host, port, user_uuid, api_key, topic, lang, disable_antimat):
        self._app = app
        self._host = host
        self._port = port
        self._user_uuid = user_uuid
        self._api_key = api_key
        self._topic = topic
        self._lang = lang
        self._disable_antimat = disable_antimat

    async def _upgrade_connection(self, conn: ProtoConnection):
        request = ('GET /asr_partial_checked HTTP/1.1\r\n'
                   'User-Agent: {app}\r\n'
                   'Host: {host}:{port}\r\n'
                   'Upgrade: dictation\r\n\r\n'
                   ).format(app=self._app, host=self._host, port=self._port).encode("utf-8")
        conn.logger.debug('Start a connection upgrade')
        await conn.send(request)

        answer = await conn.reader.readuntil(b'\r\n\r\n')
        if not answer.decode('utf-8').startswith('HTTP/1.1 101 Switching Protocols'):
            raise TransportError('Unable to upgrade connection')
        conn.logger.debug('The connection upgrade was successful')

    async def _send_connection_request(self, conn: ProtoConnection):
        advanced_asr_options = AdvancedASROptions(
            partial_results=True,
            # beam=-1,
            # lattice_beam=-1,
            # lattice_nbest=-1,
            utterance_silence=120,
            # allow_multi_utt=True,
            # chunk_process_limit=100,
            # cmn_window=600,
            # cmn_latency=150,
            capitalize=False,
            expected_num_count=0,
            # grammar=,
            # srgs=,
            biometry='gender,age,group,children,emotion',
            use_snr=False,
            # snr_flags=,
            # biometry_group=,
            manual_punctuation=False
        )

        request = ConnectionRequest(
            speechkitVersion='',
            serviceName='asr_dictation',
            uuid=self._user_uuid,
            apiKey=self._api_key,
            applicationName=self._app,
            device='desktop',
            coords='0, 0',
            topic=self._topic,
            lang=self._lang,
            format='audio/x-pcm;bit=16;rate=16000',
            punctuation=True,
            disableAntimatNormalizer=self._disable_antimat,
            advancedASROptions=advanced_asr_options
        )

        conn.logger.debug('Start a connection init')
        await conn.send_protobuf(request)

        orig_protobuf_types = conn.protocol.protobuf_types
        conn.protocol.protobuf_types = [ConnectionResponse]
        message = await conn.recv_protobuf()
        conn.protocol.protobuf_types = orig_protobuf_types

        if message.responseCode != 200:
            raise YandexProtoConnectionHandler.error_from_response(message, 'Wrong response from server')
        conn.logger.debug('The connection init was successful')

    @staticmethod
    def error_from_response(response, text):
        error_text = '{}, status_code={}'.format(text, response.responseCode)
        if response.HasField("message"):
            error_text += ', message is "{}"'.format(response.message)
        return TransportError(error_text)

    async def on_connect(self, conn: ProtoConnection):
        await self._upgrade_connection(conn)
        await self._send_connection_request(conn)


class YandexProtoConnection(ProtoConnection):
    def __init__(self, reader: asyncio.streams.StreamReader, writer: asyncio.streams.StreamWriter,
                 handler: YandexProtoConnectionHandler, protocol: YandexSerrializeProtocol, logger, is_server):
        super().__init__(reader, writer, handler, protocol, logger, is_server)

    async def send_audio_data(self, data):
        if data is None:
            self._logger.debug('Start send finished audio data chank')
            await self.send_protobuf(AddData(lastChunk=True))
        else:
            self._logger.debug('Start send audio data (%d)', len(data))
            await self.send_protobuf(AddData(lastChunk=False, audioData=data))
