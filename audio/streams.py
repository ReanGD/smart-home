import _portaudio as pa
from collections import deque
from time import sleep
from .stream_settings import StreamSettings
from .audio_data import AudioData
from .types import paContinue


class Stream(object):
    def __init__(self, settings: StreamSettings):
        if settings is None:
            self._settings = StreamSettings()
        else:
            self._settings = settings
        self._frames_ratio = float(self._settings.sample_rate) / 1000.0

    def __enter__(self):
        return self

    def __exit__(self, value_type, value, traceback):
        self.close()

    def get_settings(self) -> StreamSettings:
        return self._settings

    def get_frames_count_by_duration_ms(self, ms):
        return int(ms * self._frames_ratio)

    def read(self, ms):
        raise Exception('Not implementation read')

    def close(self):
        raise Exception('Not implementation close')


class Microphone(Stream):
    def __init__(self, settings: StreamSettings = None):
        super().__init__(settings)

        # 5 sec
        self._audio_buffer = deque(maxlen=500)

        s = self.get_settings()
        arguments = {
            'rate': s.sample_rate,
            'channels': s.channels,
            'format': s.sample_format,
            'input': True,
            'output': False,
            'input_device_index': s.device_index,
            'output_device_index': None,
            'frames_per_buffer': s.get_frames_count_by_duration_ms(10),
            'stream_callback': self._audio_callback}

        self._stream = pa.open(**arguments)
        pa.start_stream(self._stream)

    def _audio_callback(self, data, frame_count, time_info, status):
        self._audio_buffer.append(data)
        return None, paContinue

    def read(self, ms=10):
        if self._stream is None:
            raise RuntimeError('Stream is closed')
        cnt_buffers = ms // 10
        while len(self._audio_buffer) < cnt_buffers:
            sleep(0.001)

        return b''.join([self._audio_buffer.popleft() for _ in range(cnt_buffers)])

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

    def read(self, ms):
        start = self._offset
        self._offset += (self.get_frames_count_by_duration_ms(ms) * self._settings.sample_width)
        return self._stream[start:self._offset]

    def close(self):
        self._stream = b''
        self._offset = 0


class WavStream(DataStream):
    def __init__(self, file, out_settings: StreamSettings):
        super().__init__(AudioData.load_as_wav(file, out_settings))
