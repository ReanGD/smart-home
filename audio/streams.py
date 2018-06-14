import _portaudio as pa
from .stream_settings import StreamSettings
from .audio_data import AudioData


class Stream(object):
    def __init__(self, settings: StreamSettings):
        if settings is None:
            self._settings = StreamSettings()
        else:
            self._settings = settings

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def get_settings(self) -> StreamSettings:
        return self._settings

    def read(self, num_frames):
        raise Exception('Not implementation read')

    def close(self):
        raise Exception('Not implementation close')


class Microphone(Stream):
    def __init__(self, settings: StreamSettings = None):
        super().__init__(settings)
        s = self.get_settings()
        arguments = {
            'rate': s.sample_rate,
            'channels': s.channels,
            'format': s.sample_format,
            'input': True,
            'output': False,
            'input_device_index': s.device_index,
            'output_device_index': None,
            'frames_per_buffer': s.frames_per_buffer}

        self._stream = pa.open(**arguments)
        pa.start_stream(self._stream)

    def read(self, num_frames):
        if self._stream is None:
            raise RuntimeError('Stream is closed')
        return pa.read_stream(self._stream, num_frames, False)

    def close(self):
        try:
            if not pa.is_stream_stopped(self._stream):
                pa.stop_stream(self._stream)
        finally:
            pa.close(self._stream)
            self._stream = None


class DataStream(Stream):
    def __init__(self, data: AudioData):
        super().__init__(data.get_settings())
        self._stream = data.get_raw_data()
        self._offset = 0

    def read(self, num_frames):
        start = self._offset
        self._offset += (num_frames * self._settings.sample_width)
        return self._stream[start:self._offset]

    def close(self):
        self._stream = b''
        self._offset = 0


class WavStream(DataStream):
    def __init__(self, file, out_settings: StreamSettings):
        super().__init__(AudioData.load_as_wav(file, out_settings))
