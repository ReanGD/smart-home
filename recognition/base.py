from audio.stream_settings import StreamSettings
from .audio_settings import AudioSettings


class PhraseRecognizer(object):
    def __init__(self, config):
        self._config = config
        self._data_arr = []

    def get_audio_settings(self) -> AudioSettings:
        raise Exception('Not implemented "get_audio_settings"')

    def get_config(self):
        return self._config

    async def _recognize_start(self):
        raise Exception('Not implemented "_recognize_start"')

    async def recognize_start(self):
        self._data_arr = []
        await self._recognize_start()

    async def _add_data(self, data):
        raise Exception('Not implemented "_add_data"')

    async def recognize_add_frames(self, raw_frame):
        self._data_arr.append(raw_frame)
        await self._add_data(raw_frame)

    def recognize_finish(self):
        raise Exception('Not implemented "recognize_finish"')

    def get_all_data(self):
        return b''.join(self._data_arr)

    def close(self):
        pass


class HotwordRecognizer(object):
    def __init__(self, config):
        self._config = config

    def get_audio_settings(self) -> AudioSettings:
        raise Exception('Not implemented "get_audio_settings"')

    def start(self):
        pass

    def is_hotword(self, raw_frames) -> bool:
        raise Exception('Not implemented "is_hotword"')


class VADRecognizer(object):
    def __init__(self, config):
        self._config = config

    def get_audio_settings(self) -> AudioSettings:
        raise Exception('Not implemented "get_audio_settings"')

    def is_speech(self, raw_frames) -> bool:
        raise Exception('Not implemented "is_speech"')


class PhraseRecognizerConfig(object):
    def create_phrase_recognizer(self) -> PhraseRecognizer:
        raise Exception('Not implemented "create_phrase_recognizer"')


class HotwordRecognizerConfig(object):
    def create_hotword_recognizer(self) -> HotwordRecognizer:
        raise Exception('Not implemented "create_hotword_recognizer"')


class VADRecognizerConfig(object):
    def create_vad_recognizer(self) -> VADRecognizer:
        raise Exception('Not implemented "create_vad_recognizer"')
