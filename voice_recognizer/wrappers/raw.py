from voice_recognizer.stream_settings import StreamSettings
from voice_recognizer.audio_data import AudioData
from voice_recognizer.wrappers.recognizer import RecognizerSettings, Recognizer


class Raw(Recognizer):
    def __init__(self, settings):
        super().__init__(settings)
        self._audio_data = None

    def recognize_start(self, data_settings: StreamSettings):
        self._audio_data = AudioData(b'', data_settings)

    def recognize_add_frames(self, raw_frames):
        self._audio_data.add_raw_data(b''.join(raw_frames))

    def recognize_finish(self) -> AudioData:
        return self._audio_data


class RawConfig(RecognizerSettings):
    def __init__(self):
        pass

    def create_recognizer(self):
        return Raw(self)
