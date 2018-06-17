from audio import paInt16, Stream
from .audio_settings import AudioSettings
from .yandex_api import Api, YandexApiError
from .base import PhraseRecognizer, PhraseRecognizerConfig


class Yandex(PhraseRecognizer):
    def __init__(self, config):
        audio_settings = AudioSettings(channels=1, sample_format=paInt16, sample_rate=16000)
        super().__init__(config, audio_settings)
        self._api = Api()
        self._recv_callback = None
        self._last_text = ''
        self._is_continue = False

    async def _on_recv(self, response):
        is_phrase_finished = response.endOfUtt
        recognition = response.recognition
        if not is_phrase_finished:
            if len(recognition) != 1:
                raise YandexApiError('len(recognition) != 1')

        phrases = [' '.join([word.value for word in phrase.words]) for phrase in recognition]

        if not is_phrase_finished and self._last_text == phrases[0]:
            return True
        else:
            self._last_text = phrases[0]

        self._is_continue = await self._recv_callback(phrases, is_phrase_finished, response)
        return self._is_continue

    async def recognize(self, stream: Stream, recv_callback):
        self._is_continue = True
        self._recv_callback = recv_callback
        c = self.get_config()
        await self._api.connect(c.app, c.host, c.port, c.user_uuid, c.api_key, c.topic, c.lang,
                                c.disable_antimat)

        await self._api.recv_loop_run(self._on_recv)
        while self._is_continue:
            await self._api.send_audio_data(await stream.read(50))

        self._api.close()
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
