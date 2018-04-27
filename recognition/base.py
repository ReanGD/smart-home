from audio.stream_settings import StreamSettings
from .audio_settings import AudioSettings


class PhraseRecognizer(object):
    def __init__(self, config):
        self._config = config

    def get_audio_settings(self) -> AudioSettings:
        raise Exception('Not implemented "get_audio_settings"')

    def recognize_start(self, data_settings: StreamSettings):
        raise Exception('Not implemented "recognize_start"')

    def recognize_add_frames(self, raw_frames):
        raise Exception('Not implemented "recognize_add_data"')

    def recognize_finish(self):
        raise Exception('Not implemented "recognize_finish"')


class HotwordRecognizer(object):
    def __init__(self, config):
        self._config = config

    def get_audio_settings(self) -> AudioSettings:
        raise Exception('Not implemented "get_audio_settings"')

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
