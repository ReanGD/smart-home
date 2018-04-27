from audio import StreamSettings, AudioData
from .base import PhraseRecognizer, PhraseRecognizerConfig
from .audio_settings import AudioSettings


class Raw(PhraseRecognizer):
    def __init__(self, config):
        super().__init__(config)
        self._audio_data = None

    def get_audio_settings(self) -> AudioSettings:
        return AudioSettings()

    def recognize_start(self, data_settings: StreamSettings):
        self._audio_data = AudioData(b'', data_settings)

    def recognize_add_frames(self, raw_frames):
        self._audio_data.add_raw_data(b''.join(raw_frames))

    def recognize_finish(self) -> AudioData:
        return self._audio_data


class RawConfig(PhraseRecognizerConfig):
    def __init__(self):
        pass

    def create_phrase_recognizer(self):
        return Raw(self)
