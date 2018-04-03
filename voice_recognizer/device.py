import pyaudio
from voice_recognizer.streams import MicrophoneStream, DataStream
from voice_recognizer.stream_settings import StreamSettings
from voice_recognizer.audio_data import AudioData


class Device(object):
    def __init__(self):
        self._device = pyaudio.PyAudio()
        self._streams = []

    def get_device_count(self) -> int:
        return self._device.get_device_count()

    def get_device_info_by_index(self, device_index):
        if device_index is not None:
            return self._device.get_device_info_by_index(device_index)
        else:
            return self._device.get_default_input_device_info()

    def find_device_index(self, name_start_with):
        for i in range(self._device.get_device_count()):
            device_info = self._device.get_device_info_by_index(i)
            if device_info["name"].startswith(name_start_with):
                return i

        return None

    @staticmethod
    def _print_microphone_info(device_info):
        print(device_info["name"])
        for ind, name in device_info.items():
            print("{}: {}".format(ind, name))

    def print_microphones_info(self):
        Device._print_microphone_info(self._device.get_default_input_device_info())

        for i in range(self._device.get_device_count()):
            self._device.get_default_input_device_info()
            device_info = self._device.get_device_info_by_index(i)
            if device_info["maxInputChannels"] != 0:
                print()
                Device._print_microphone_info(device_info)

    def create_microphone_stream(self, settings: StreamSettings):
        stream = self._device.open(input_device_index=settings.device_index,
                                   channels=settings.channels,
                                   format=settings.sample_format,
                                   rate=settings.sample_rate,
                                   frames_per_buffer=settings.frames_per_buffer,
                                   input=True,
                                   stream_callback=None)

        mic_stream = MicrophoneStream(stream, settings)
        self._streams.append(mic_stream)
        return mic_stream

    def create_data_stream(self, data: AudioData):
        data_stream = DataStream(data.get_raw_data(), data.get_settings())
        self._streams.append(data_stream)
        return data_stream

    def close_streams(self):
        for stream in self._streams:
            stream.close()
        self._streams.clear()

    def terminate(self):
        self.close_streams()
        self._device.terminate()
