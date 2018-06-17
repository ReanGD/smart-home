import asyncio
from audio import StreamSettings, paInt16
from .audio_settings import AudioSettings
from .yandex_api import Api, YandexApiError
from .base import PhraseRecognizer, PhraseRecognizerConfig


class ApiWrapper(object):
    def __init__(self, config, result_callback, finish_result_callback):
        self._config = config
        self._api = Api()
        self._recv_task = None
        self._result_callback = result_callback
        self._finish_result_callback = finish_result_callback
        self._last_text = ''

    async def connect(self):
        c = self._config
        await self._api.connect(c.app, c.host, c.port, c.user_uuid, c.api_key, c.topic, c.lang,
                                c.disable_antimat)
        self._recv_task = asyncio.ensure_future(self._api.recv_loop(self._recv_callback))

    async def send_audio_data(self, data):
        await self._api.send_audio_data(data)

    async def _recv_callback(self, response):
        if response.endOfUtt:
            await self._finish_result_callback(response)
        else:
            if len(response.recognition) != 1:
                raise YandexApiError('len(recognition) != 1')

            phrase = response.recognition[0]
            if phrase.confidence != 1.0:
                raise YandexApiError('phrase.confidence != 1')
            elif len(phrase.words) != 1:
                raise YandexApiError('len(words) != 1')

            word = phrase.words[0]
            if word.confidence != 1.0:
                raise YandexApiError('word.confidence != 1')

            if self._last_text != word.value:
                self._last_text = word.value
                await self._result_callback(word.value)

    def close(self):
        if self._recv_task is not None:
            self._recv_task.cancel()
            self._recv_task = None

        if self._api is not None:
            self._api.close()
            self._api = None

        self._last_text = ''


class Yandex(PhraseRecognizer):
    def __init__(self, config):
        super().__init__(config)
        self._audio_settings = AudioSettings(channels=1, sample_format=paInt16, sample_rate=16000)
        self._api = ApiWrapper(self.get_config(), self._recv_result, self._recv_finish_result)

    def get_audio_settings(self) -> AudioSettings:
        return self._audio_settings

    async def _recv_result(self, text):
        print(text)

    async def _recv_finish_result(self, response):
        if len(response.recognition) != 0:
            for bio in response.bioResult:
                print('{} {} {}'.format(bio.classname, bio.confidence, bio.tag))

        for ind, phrase in enumerate(response.recognition):
            words = ['{}({})'.format(word.value, word.confidence) for word in phrase.words]
            print('{}: {}'.format(ind, ':'.join(words)))

    async def _recognize_start(self):
        await self._api.connect()

    async def _add_data(self, data):
        await self._api.send_audio_data(data)

    def recognize_finish(self):
        pass

    def close(self):
        if self._api:
            self._api.close()
            self._api = None


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
