from logging import getLogger
from etc import YanexTransportConfig
from audio import PA_INT16, Stream, AudioSettings, SettingsConverter
from protocols.transport import TransportError
from protocols.yandex import YandexSerrializeProtocol, YandexClient, AddDataResponse
from .base import PhraseRecognizer, PhraseRecognizerConfig


class Yandex(PhraseRecognizer, YandexClient):
    def __init__(self, cfg: 'YandexConfig'):
        self._logger = getLogger('yandex_api')
        self._recv_callback = None
        self._last_text = ''
        self._is_continue = False

        audio_settings = AudioSettings(channels=1, sample_format=PA_INT16, sample_rate=16000)
        PhraseRecognizer.__init__(self, cfg, audio_settings)
        YandexClient.__init__(self, self._logger, cfg.address, cfg.app, cfg.user_uuid,
                              cfg.api_key, cfg.topic, cfg.lang, cfg.disable_antimat)

    async def on_add_data_response(self, response: AddDataResponse):
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

        protocol = YandexSerrializeProtocol([AddDataResponse], self._logger)
        await self.connect(protocol, max_attempt=6)

        while self._is_continue:
            await self.send_audio_data(await stream.read_full(50))

        await self.close()
        self._last_text = ''


class YandexConfig(PhraseRecognizerConfig):
    def __init__(self, api_key, user_uuid, topic='queries', lang='ru-RU', disable_antimat=True):
        self.api_key = api_key
        self.user_uuid = user_uuid
        self.topic = topic
        self.lang = lang
        self.disable_antimat = disable_antimat
        self.app = 'SmartHome'
        self.address = YanexTransportConfig()

    def create_phrase_recognizer(self):
        return Yandex(self)
