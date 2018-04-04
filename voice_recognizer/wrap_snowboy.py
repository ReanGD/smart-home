import pyaudio
from voice_recognizer.device import Device
from voice_recognizer.stream_settings import StreamSettings
import external.snowboy.snowboydetect as snowboydetect


class SnowboyWrap(object):
    def __init__(self, resource_filename, model_str, sensitivity=0.5, audio_gain=1.0):
        self._detector = snowboydetect.SnowboyDetect(resource_filename=resource_filename.encode(),
                                                     model_str=model_str.encode())
        self._sensitivity = sensitivity
        self.set_sensitivity(sensitivity)
        self._audio_gain = audio_gain
        self.set_audio_gain(audio_gain)

    def set_audio_gain(self, value):
        self._audio_gain = value
        self._detector.SetAudioGain(value)

    def get_audio_gain(self):
        return self._audio_gain

    def set_sensitivity(self, value):
        self._sensitivity = value
        num_hotwords = self._detector.NumHotwords()
        self._detector.SetSensitivity(",".join([str(value)] * num_hotwords).encode())

    def get_sensitivity(self):
        return self._sensitivity

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
