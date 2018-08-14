from logging import getLogger
from audio import paInt16, Stream, AudioData, StreamSettings
from .audio_settings import AudioSettings
from protocols.transport import create_client, ProtoTransportError
from protocols.yandex import *
from .base import PhraseRecognizer, PhraseRecognizerConfig


class Handler(YandexProtoConnectionHandler):
    def set_callback(self, callback):
        self._callback = callback

    async def on_add_data_response(self, conn, message: AddDataResponse):
        await self._callback(message)


class Yandex(PhraseRecognizer):
    def __init__(self, config):
        audio_settings = AudioSettings(channels=1, sample_format=paInt16, sample_rate=16000)
        super().__init__(config, audio_settings)
        self._connection = None
        self._recv_callback = None
        self._last_text = ''
        self._is_continue = False
        self._yandex_settings = StreamSettings(channels=1, sample_format=paInt16, sample_rate=16000)

    async def _on_recv(self, response: AddDataResponse):
        is_phrase_finished = response.endOfUtt
        recognition = response.recognition
        if not is_phrase_finished:
            if len(recognition) != 1:
                raise ProtoTransportError('len(recognition) != 1')

        phrases = [' '.join([word.value for word in phrase.words]) for phrase in recognition]

        if not is_phrase_finished and self._last_text == phrases[0]:
            return True
        else:
            self._last_text = phrases[0]

        self._is_continue = await self._recv_callback(phrases, is_phrase_finished, response)
        return self._is_continue

    async def recognize(self, stream: Stream, recv_callback):
        stream.start_stream()
        stream.crop_to(100)
        self._is_continue = True
        self._recv_callback = recv_callback
        c = self.get_config()

        logger = getLogger('yandex_api')
        protocol = YandexSerrializeProtocol([AddDataResponse], logger)

        def handler_factory():
            handler = Handler(c.app, c.host, c.port, c.user_uuid, c.api_key, c.topic, c.lang, c.disable_antimat)
            handler.set_callback(self._on_recv)
            return handler

        self._connection = await create_client(c.host, c.port, handler_factory, protocol, logger, YandexProtoConnection)

        while self._is_continue:
            data = AudioData(await stream.read_full(50), stream.get_settings()).get_raw_data(self._yandex_settings)
            await self._connection.send_audio_data(data)

        await self._connection.close()
        self._last_text = ''


class YandexConfig(PhraseRecognizerConfig):
    def __init__(self, api_key, user_uuid, topic='queries', lang='ru-RU', disable_antimat=True):
        self.api_key = api_key
        self.user_uuid = user_uuid
        self.topic = topic
        self.lang = lang
        self.disable_antimat = disable_antimat
        self.host = 'asr.yandex.net'
        self.port = 443
        self.app = 'SmartHome'

    def create_phrase_recognizer(self):
        return Yandex(self)
