import pyaudio
from .stream_settings import StreamSettings
from .audio_data import AudioData


class Stream(object):
    def __init__(self, settings: StreamSettings):
        self._settings = settings

    def get_settings(self) -> StreamSettings:
        return self._settings

    def read(self, num_frames):
        raise Exception('Not implementation read')

    def close(self):
        raise Exception('Not implementation close')


class MicrophoneStream(Stream):
    def __init__(self, steam: pyaudio.Stream, settings: StreamSettings):
        super().__init__(settings)
        self._stream = steam

    def read(self, num_frames):
        return self._stream.read(num_frames, exception_on_overflow=False)

    def close(self):
        try:
            if not self._stream.is_stopped():
                self._stream.stop_stream()
        finally:
            self._stream.close()


class MicrophoneSavedStream(MicrophoneStream):
    def __init__(self, steam: pyaudio.Stream, settings: StreamSettings):
        super().__init__(steam, settings)
        self._data = []

    def read(self, num_frames):
        frames = super().read(num_frames)
        self._data.append(frames)
        return frames

    def get_data(self) -> AudioData:
        return AudioData(b''.join(self._data), self._settings)


class DataStream(Stream):
    def __init__(self, raw_data, settings: StreamSettings):
        super().__init__(settings)
        self._stream = raw_data
        self._offset = 0

    def read(self, num_frames):
        start = self._offset
        self._offset += (num_frames * self._settings.sample_width)
        return self._stream[start:self._offset]

    def close(self):
        self._stream = b''
