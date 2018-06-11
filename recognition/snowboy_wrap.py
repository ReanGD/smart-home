from pyaudio import get_format_from_width
from snowboy.snowboydetect import SnowboyDetect
from .base import HotwordRecognizer, VADRecognizer, HotwordRecognizerConfig, VADRecognizerConfig
from .audio_settings import AudioSettings


class Snowboy(HotwordRecognizer, VADRecognizer):
    def __init__(self, config):
        super().__init__(config)
        self._detector = SnowboyDetect(config.resource_path.encode(), config.model_path.encode())
        self.set_sensitivity(self._config.sensitivity)
        self.set_audio_gain(self._config.audio_gain)

        channels = self._detector.NumChannels()
        sample_format = get_format_from_width(self._detector.BitsPerSample() / 8)
        sample_rate = self._detector.SampleRate()
        self._audio_settings = AudioSettings(channels, sample_format, sample_rate)

    def get_audio_settings(self) -> AudioSettings:
        return self._audio_settings

    def set_audio_gain(self, value):
        self._config.audio_gain = value
        self._detector.SetAudioGain(value)

    def get_audio_gain(self):
        return self._config.audio_gain

    def set_sensitivity(self, value):
        self._config.sensitivity = value
        num_hotwords = self._detector.NumHotwords()
        self._detector.SetSensitivity(",".join([str(value)] * num_hotwords).encode())

    def get_sensitivity(self):
        return self._config.sensitivity

    def detect(self, raw_frames):
        result = self._detector.RunDetection(raw_frames)
        assert result != -1, "Error initializing streams or reading audio data"
        return result

    def is_hotword(self, raw_frames):
        return self.detect(raw_frames) > 0

    def is_speech(self, raw_frames):
        return self.detect(raw_frames) >= 0


class SnowboyConfig(HotwordRecognizerConfig, VADRecognizerConfig):
    def __init__(self, resource_path, model_path, sensitivity=0.5, audio_gain=1.0):
        self.resource_path = resource_path
        self.model_path = model_path
        self.sensitivity = sensitivity
        self.audio_gain = audio_gain
        self._cache = None

    def create_hotword_recognizer(self):
        if self._cache is None:
            self._cache = Snowboy(self)

        return self._cache

    def create_vad_recognizer(self):
        if self._cache is None:
            self._cache = Snowboy(self)

        return self._cache
