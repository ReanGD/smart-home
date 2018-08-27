from logging import getLogger
from audio import PA_INT16, Stream, AudioSettings, SettingsConverter
from protocols.transport import TransportError
from protocols.yandex import YandexSerrializeProtocol, YandexClient, AddDataResponse
from .base import PhraseRecognizer, PhraseRecognizerConfig


class Client(YandexClient):
    def __init__(self, logger, callback, cfg: 'YandexConfig'):
        super().__init__(logger, cfg.app, cfg.host, cfg.port, cfg.user_uuid, cfg.api_key, cfg.topic,
                         cfg.lang, cfg.disable_antimat)
        self._callback = callback

    async def on_add_data_response(self, message: AddDataResponse):
        await self._callback(message)


class Yandex(PhraseRecognizer):
    def __init__(self, config):
        super().__init__(config, AudioSettings(channels=1, sample_format=PA_INT16, sample_rate=16000))
        self._recv_callback = None
        self._last_text = ''
        self._is_continue = False

        self._logger = getLogger('yandex_api')
        self._connection = Client(self._logger, self._on_recv, config)

    async def _on_recv(self, response: AddDataResponse):
        if response.responseCode != 200:
            raise TransportError('Wrong responce code ({}) for AddData'.format(response.responseCode))

        is_phrase_finished = response.endOfUtt
        recognition = response.recognition
        if not is_phrase_finished:
            if len(recognition) == 0:
                self._is_continue = True
                return self._is_continue
            if len(recognition) != 1:
                raise TransportError('len(recognition) != 1')

        phrases = [' '.join([word.value for word in phrase.words]) for phrase in recognition]

        if not is_phrase_finished and self._last_text == phrases[0]:
            return True
        else:
            self._last_text = phrases[0]

        self._is_continue = await self._recv_callback(phrases, is_phrase_finished, response)
        return self._is_continue

    async def recognize(self, stream: Stream, recv_callback):
        stream = SettingsConverter(stream, self.get_audio_settings())
        stream.start_stream()
        stream.crop_to(100)
        self._is_continue = True
        self._recv_callback = recv_callback
        cfg = self.get_config()

        protocol = YandexSerrializeProtocol([AddDataResponse], self._logger)
        await self._connection.connect(cfg.host, cfg.port, protocol)

        while self._is_continue:
            await self._connection.send_audio_data(await stream.read_full(50))

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
