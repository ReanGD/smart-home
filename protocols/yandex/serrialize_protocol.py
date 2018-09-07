import asyncio
from logging import Logger
from google.protobuf import message as gp_message
from protocols.transport import TransportError, SerrializeProtocol, TCPClientConnection
from .basic_pb2 import ConnectionResponse
from .voiceproxy_pb2 import AdvancedASROptions, ConnectionRequest, AddData


class YandexSerrializeProtocol(SerrializeProtocol):
    async def send(self, writer: asyncio.streams.StreamWriter, message: gp_message) -> None:
        message_bin = message.SerializeToString()
        message_len = len(message_bin)
        message_name = message.DESCRIPTOR.name

        self._logger.debug('Send protobuf message "%s" (%d bytes)', message_name, message_len)
        writer.write(hex(message_len)[2:].encode('utf-8'))
        writer.write(b'\r\n')
        writer.write(message_bin)
        await writer.drain()

    async def recv(self, reader: asyncio.streams.StreamReader) -> gp_message:
        # pylint: disable=broad-except
        package_size_bin = await reader.readuntil(b'\r\n')
        package_size = int(b'0x' + package_size_bin[:-2], 0)
        package_bin = await reader.readexactly(package_size)

        for proto_type in self._protobuf_types:
            message = proto_type()
            try:
                message.ParseFromString(package_bin)
                self._logger.debug('Recv protobuf message "%s" (%d bytes)',
                                   message.DESCRIPTOR.name, package_size)
                return message
            except Exception:
                pass

        self._logger.debug('Recv unknown protobuf message (%d bytes)', package_size)
        raise TransportError('Recv unknown protobuf message')


class YandexClient(TCPClientConnection):
    def __init__(self, logger: Logger, app: str, host: str, port: int, user_uuid: str,
                 api_key: str, topic: str, lang: str, disable_antimat: bool):
        # pylint: disable=too-many-arguments
        super().__init__(logger)
        self._app = app
        self._host = host
        self._port = port

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

        self._connection_request = ConnectionRequest(
            speechkitVersion='',
            serviceName='asr_dictation',
            uuid=user_uuid,
            apiKey=api_key,
            applicationName=app,
            device='desktop',
            coords='0, 0',
            topic=topic,
            lang=lang,
            format='audio/x-pcm;bit=16;rate=16000',
            punctuation=True,
            disableAntimatNormalizer=disable_antimat,
            advancedASROptions=advanced_asr_options
        )

    async def __upgrade_connection(self) -> None:
        request = ('GET /asr_partial_checked HTTP/1.1\r\n'
                   'User-Agent: {app}\r\n'
                   'Host: {host}:{port}\r\n'
                   'Upgrade: dictation\r\n\r\n'
                   ).format(app=self._app, host=self._host, port=self._port).encode("utf-8")
        self._logger.debug('Start a connection upgrade')

        self._writer.write(request)
        await self._writer.drain()

        answer = await self._reader.readuntil(b'\r\n\r\n')
        if not answer.decode('utf-8').startswith('HTTP/1.1 101 Switching Protocols'):
            raise TransportError('Unable to upgrade connection')
        self._logger.debug('The connection upgrade was successful')

    async def __send_connection_request(self) -> None:
        self._logger.debug('Start a connection init')
        await self.send(self._connection_request)

        orig_protobuf_types = self._protocol.protobuf_types
        self._protocol.protobuf_types = [ConnectionResponse]
        message = await self.recv()
        self._protocol.protobuf_types = orig_protobuf_types

        if message.responseCode != 200:
            raise YandexClient.error_from_response(message, 'Wrong response from server')
        self._logger.debug('The connection init was successful')

    @staticmethod
    def error_from_response(response: gp_message, text: str) -> TransportError:
        error_text = '{}, status_code={}'.format(text, response.responseCode)
        if response.HasField("message"):
            error_text += ', message is "{}"'.format(response.message)
        return TransportError(error_text)

    async def on_connect(self) -> None:
        await self.__upgrade_connection()
        await self.__send_connection_request()

    async def send_audio_data(self, data: bytes) -> None:
        if data is None:
            self._logger.debug('Start send finished audio data chank')
            await self.send(AddData(lastChunk=True))
        else:
            self._logger.debug('Start send audio data (%d)', len(data))
            await self.send(AddData(lastChunk=False, audioData=data))
