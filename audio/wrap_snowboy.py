import pyaudio
from .device import Device
from .stream_settings import StreamSettings
import external.snowboy.snowboydetect as snowboydetect


class SnowboyConfig(object):
    def __init__(self, resource_path, model_path, sensitivity=0.5, audio_gain=1.0):
        self.resource_path = resource_path
        self.model_path = model_path
        self.sensitivity = sensitivity
        self.audio_gain = audio_gain


class SnowboyWrap(object):
    def __init__(self, config: SnowboyConfig):
        self._config = config
        self._detector = snowboydetect.SnowboyDetect(config.resource_path.encode(),
                                                     config.model_path.encode())
        self.set_sensitivity(self._config.sensitivity)
        self.set_audio_gain(self._config.audio_gain)

    def get_config(self):
        return self._config

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

    def get_audio_settings(self,
                           device: Device,
                           device_index=None,
                           frames_per_buffer=2048) -> StreamSettings:

        channels = self._detector.NumChannels()
        sample_format = pyaudio.get_format_from_width(self._detector.BitsPerSample() / 8)
        sample_rate = self._detector.SampleRate()

        return StreamSettings(device,
                              device_index=device_index,
                              channels=channels,
                              sample_format=sample_format,
                              sample_rate=sample_rate,
                              frames_per_buffer=frames_per_buffer)

    def detect(self, frames):
        result = self._detector.RunDetection(frames)
        assert result != -1, "Error initializing streams or reading audio data"
        return result

    def is_hotword(self, frames):
        return self.detect(frames) > 0

    def is_speech(self, frames):
        return self.detect(frames) >= 0
