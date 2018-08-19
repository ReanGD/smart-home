import wave
from io import BytesIO
import _portaudio as pa
from threading import Lock
from collections import deque
from asyncio import Future, get_event_loop
from .types import paContinue, paInt16, get_format_from_width
from .helper import audio_data_converter
from .settings import AudioSettings
from .devices import Devices


class Stream(object):
    def __init__(self, settings: AudioSettings):
        self._settings = settings
        self._frames_ratio = float(self._settings.sample_rate) / 1000.0

    def __enter__(self):
        return self

    def __exit__(self, value_type, value, traceback):
        self.close()

    def get_settings(self) -> AudioSettings:
        return self._settings

    def get_frames_count_by_duration_ms(self, ms):
        return int(ms * self._frames_ratio)

    def start_stream(self):
        raise Exception('Not implementation "start_stream"')

    async def read(self, ms):
        raise Exception('Not implementation "read"')

    async def read_full(self, min_ms):
        raise Exception('Not implementation "read_full"')

    def crop_to(self, ms):
        raise Exception('Not implementation "crop_to"')

    def close(self):
        raise Exception('Not implementation "close"')


class SettingsConverter(Stream):
    def __init__(self, in_stream: Stream, out_settings: AudioSettings):
        super().__init__(out_settings)
        self._in_stream = in_stream

    def start_stream(self):
        self._in_stream.start_stream()

    async def read(self, ms):
        data = await self._in_stream.read(ms)
        return audio_data_converter(data, self._in_stream.get_settings(), self.get_settings())

    async def read_full(self, min_ms):
        data = await self._in_stream.read_full(min_ms)
        return audio_data_converter(data, self._in_stream.get_settings(), self.get_settings())

    def crop_to(self, ms):
        self._in_stream.crop_to(ms)

    def close(self):
        self._in_stream.close()


class Storage(Stream):
    def __init__(self, in_stream: Stream):
        super().__init__(in_stream.get_settings())
        self._raw_data = b''
        self._in_stream = in_stream

    def start_stream(self):
        self._in_stream.start_stream()

    async def read(self, ms):
        data = await self._in_stream.read(ms)
        self._raw_data += data
        return data

    async def read_full(self, min_ms):
        data = await self._in_stream.read_full(min_ms)
        self._raw_data += data
        return data

    def crop_to(self, ms):
        self._in_stream.crop_to(ms)

    def close(self):
        self._in_stream.close()

    def save_as_wav(self, file):
        wav_writer = wave.open(file, "wb")
        try:
            s = self.get_settings()
            wav_writer.setnchannels(s.channels)
            wav_writer.setsampwidth(s.sample_width)
            wav_writer.setframerate(s.sample_rate)
            wav_writer.writeframes(self._raw_data)
        finally:
            wav_writer.close()

    def get_raw_data(self):
        return self._raw_data

    def get_wav_data(self):
        file = BytesIO()
        self.save_as_wav(file)
        return file.getvalue()


class Microphone(Stream):
    def __init__(self,
                 device_index: int=None,
                 channels: int=1,
                 sample_format=paInt16,
                 sample_rate: int=None):

        device_info = Devices.get_device_info_by_index(device_index)
        if sample_rate is None:
            sample_rate = device_info.default_sample_rate

        super().__init__(AudioSettings(channels, sample_format, sample_rate))

        self._loop = get_event_loop()
        self._lock = Lock()
        self._waiter = None
        self._need_buffers = None

        # 5 sec
        self._audio_buffer = deque(maxlen=500)

        s = self.get_settings()
        msg = 'Param "channel" must be less than {}'.format(device_info.max_input_channels + 1)
        assert s.channels <= device_info.max_input_channels, msg

        arguments = {
            'rate': s.sample_rate,
            'channels': s.channels,
            'format': s.sample_format,
            'input': True,
            'output': False,
            'input_device_index': device_info.index,
            'output_device_index': None,
            'frames_per_buffer': s.get_frames_count_by_duration_ms(10),
            'stream_callback': self._audio_callback}

        self._stream = pa.open(**arguments)
        self._is_started = False

    def start_stream(self):
        if not self._is_started:
            if self._stream is not None:
                self._is_started = True
                pa.start_stream(self._stream)

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

    async def _wait_data(self, cnt_buffers):
        self.start_stream()

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

    async def read(self, ms=10):
        cnt_buffers = ms // 10
        await self._wait_data(cnt_buffers)
        return b''.join([self._audio_buffer.popleft() for _ in range(cnt_buffers)])

    async def read_full(self, min_ms):
        cnt_buffers = min_ms // 10
        await self._wait_data(cnt_buffers)
        return b''.join([self._audio_buffer.popleft() for _ in range(len(self._audio_buffer))])

    def crop_to(self, ms):
        total_cnt = len(self._audio_buffer)
        leave_cnt = ms // 10
        remove_cnt = max(0, total_cnt - leave_cnt)
        if remove_cnt != 0:
            for _ in range(remove_cnt):
                self._audio_buffer.popleft()

    def close(self):
        if self._stream is not None:
            try:
                if not pa.is_stream_stopped(self._stream):
                    pa.stop_stream(self._stream)
            finally:
                pa.close(self._stream)
                self._stream = None


class DataStream(Stream):
    def __init__(self, raw_data, settings: AudioSettings):
        super().__init__(settings)
        self._raw_data = raw_data
        self._offset = 0

    def start_stream(self):
        pass

    async def read(self, ms):
        start = self._offset
        self._offset += (self.get_frames_count_by_duration_ms(ms) * self._settings.sample_width)
        return self._raw_data[start:self._offset]

    async def read_full(self, min_ms):
        start = self._offset
        self._offset = len(self._raw_data)
        return self._raw_data[self._offset:]

    def crop_to(self, ms):
        pass

    def close(self):
        self._raw_data = b''
        self._offset = 0


class WavStream(DataStream):
    def __init__(self, file_path):
        wav_reader = wave.open(file_path, "rb")
        try:
            sample_format = get_format_from_width(wav_reader.getsampwidth())
            settings = AudioSettings(channels=wav_reader.getnchannels(),
                                     sample_rate=wav_reader.getframerate(),
                                     sample_format=sample_format)
            raw_data = wav_reader.readframes(wav_reader.getnframes())
            super().__init__(raw_data, settings)
        finally:
            wav_reader.close()
