import _portaudio as pa
from threading import Lock
from collections import deque
from asyncio import Future, get_event_loop
from .types import paContinue
from .audio_data import AudioData
from .stream_settings import StreamSettings


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

    async def read(self, ms):
        raise Exception('Not implementation read')

    def close(self):
        raise Exception('Not implementation close')


class Microphone(Stream):
    def __init__(self, settings: StreamSettings = None):
        super().__init__(settings)
        self._loop = get_event_loop()
        self._lock = Lock()
        self._waiter = None
        self._need_buffers = None

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
        self._is_started = False

    def _wakeup_waiter(self):
        waiter = self._waiter
        if waiter is not None:
            self._waiter = None
            if not waiter.cancelled():
                waiter.set_result(None)

    def _audio_callback(self, data, frame_count, time_info, status):
        self._audio_buffer.append(data)
        self._lock.acquire()
        try:
            if self._need_buffers is not None and len(self._audio_buffer) >= self._need_buffers:
                self._need_buffers = None
                self._loop.call_soon_threadsafe(self._wakeup_waiter)
        finally:
            self._lock.release()

        return None, paContinue

    async def read(self, ms=10):
        if not self._is_started:
            if self._stream is not None:
                self._is_started = True
                pa.start_stream(self._stream)

        cnt_buffers = ms // 10
        if len(self._audio_buffer) < cnt_buffers:
            self._lock.acquire()
            try:
                self._need_buffers = cnt_buffers
                self._waiter = Future(loop=self._loop)
            finally:
                self._lock.release()

            if self._stream is None:
                raise RuntimeError('Stream is closed')

            try:
                await self._waiter
            finally:
                self._waiter = None

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

    async def read(self, ms):
        start = self._offset
        self._offset += (self.get_frames_count_by_duration_ms(ms) * self._settings.sample_width)
        return self._stream[start:self._offset]

    def close(self):
        self._stream = b''
        self._offset = 0


class WavStream(DataStream):
    def __init__(self, file, out_settings: StreamSettings):
        super().__init__(AudioData.load_as_wav(file, out_settings))
