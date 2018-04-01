import pyaudio
from voice_recognizer.stream_settings import StreamSettings


class MicrophoneStream(object):
    def __init__(self, steam: pyaudio.Stream, settings: StreamSettings):
        self._settings = settings
        self._stream = steam

    def read(self, num_frames):
        return self._stream.read(num_frames, exception_on_overflow=False)

    def close(self):
        try:
            if not self._stream.is_stopped():
                self._stream.stop_stream()
        finally:
            self._stream.close()
