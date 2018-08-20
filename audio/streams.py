import wave
from io import BytesIO
from threading import Lock
from collections import deque
from asyncio import Future, get_event_loop
import _portaudio as pa
from .types import PA_INT16, get_format_from_width
from .helper import audio_data_converter
from .settings import AudioSettings
from .devices import Devices


# pylint: disable=no-self-use
class Stream:
    def __init__(self, settings: AudioSettings):
        self._settings = settings

    def __enter__(self):
        return self

    def __exit__(self, value_type, value, traceback):
        self.close()

    def get_settings(self) -> AudioSettings:
        return self._settings

    def start_stream(self):
        raise Exception('Not implementation "start_stream"')

    async def read(self, _milliseconds: int) -> bytes:
        raise Exception('Not implementation "read"')

    async def read_full(self, _min_ms: int) -> bytes:
        raise Exception('Not implementation "read_full"')

    def crop_to(self, _milliseconds: int):
        raise Exception('Not implementation "crop_to"')

    def close(self):
        raise Exception('Not implementation "close"')
# pylint: enable=no-self-use


class SettingsConverter(Stream):
    def __init__(self, in_stream: Stream, out_settings: AudioSettings):
        super().__init__(out_settings)
        self._in_stream = in_stream

    def start_stream(self):
        self._in_stream.start_stream()

    async def read(self, milliseconds: int) -> bytes:
        data = await self._in_stream.read(milliseconds)
        return audio_data_converter(data, self._in_stream.get_settings(), self.get_settings())

    async def read_full(self, min_ms: int) -> bytes:
        data = await self._in_stream.read_full(min_ms)
        return audio_data_converter(data, self._in_stream.get_settings(), self.get_settings())

    def crop_to(self, milliseconds: int):
        self._in_stream.crop_to(milliseconds)

    def close(self):
        self._in_stream.close()


class Storage(Stream):
    def __init__(self, in_stream: Stream):
        super().__init__(in_stream.get_settings())
        self._raw_data = b''
        self._in_stream = in_stream

    def start_stream(self):
        self._in_stream.start_stream()

    async def read(self, milliseconds: int) -> bytes:
        data = await self._in_stream.read(milliseconds)
        self._raw_data += data
        return data

    async def read_full(self, min_ms: int) -> bytes:
        data = await self._in_stream.read_full(min_ms)
        self._raw_data += data
        return data

    def crop_to(self, milliseconds: int):
        self._in_stream.crop_to(milliseconds)

    def close(self):
        self._in_stream.close()

    def save_as_wav(self, file: [str, BytesIO]):
        wav_writer = wave.open(file, "wb")
        try:
            settings = self.get_settings()
            wav_writer.setnchannels(settings.channels)
            wav_writer.setsampwidth(settings.sample_width)
            wav_writer.setframerate(settings.sample_rate)
            wav_writer.writeframes(self._raw_data)
        finally:
            wav_writer.close()

    def get_raw_data(self) -> bytes:
        return self._raw_data

    def get_wav_data(self) -> bytes:
        file = BytesIO()
        self.save_as_wav(file)
        return file.getvalue()


class Microphone(Stream):
    def __init__(self,
                 device_index: int = None,
                 channels: int = 1,
                 sample_format: int = PA_INT16,
                 sample_rate: int = None):

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

        settings = self.get_settings()
        msg = 'Param "channel" must be less than {}'.format(device_info.max_input_channels + 1)
        assert settings.channels <= device_info.max_input_channels, msg

        arguments = {
            'rate': settings.sample_rate,
            'channels': settings.channels,
            'format': settings.sample_format,
            'input': True,
            'output': False,
            'input_device_index': device_info.index,
            'output_device_index': None,
            'frames_per_buffer': settings.get_frames_count_by_duration_ms(10),
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

    def _audio_callback(self, data: bytes, _frame_count, _time_info, _status):
        self._audio_buffer.append(data)
        self._lock.acquire()
        try:
            if self._need_buffers is not None and len(self._audio_buffer) >= self._need_buffers:
                self._need_buffers = None
                self._loop.call_soon_threadsafe(self._wakeup_waiter)
        finally:
            self._lock.release()

        return None, pa.paContinue

    async def _wait_data(self, cnt_buffers: int):
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

    async def read(self, milliseconds: int = 10) -> bytes:
        cnt_buffers = milliseconds // 10
        await self._wait_data(cnt_buffers)
        return b''.join([self._audio_buffer.popleft() for _ in range(cnt_buffers)])

    async def read_full(self, min_ms: int) -> bytes:
        cnt_buffers = min_ms // 10
        await self._wait_data(cnt_buffers)
        return b''.join([self._audio_buffer.popleft() for _ in range(len(self._audio_buffer))])

    def crop_to(self, milliseconds: int):
        total_cnt = len(self._audio_buffer)
        leave_cnt = milliseconds // 10
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
    def __init__(self, raw_data: bytes, settings: AudioSettings):
        super().__init__(settings)
        self._raw_data = raw_data
        self._offset = 0

    def start_stream(self):
        pass

    async def read(self, milliseconds: int) -> bytes:
        start = self._offset
        frames = self.get_settings().get_frames_count_by_duration_ms(milliseconds)
        self._offset += (frames * self._settings.sample_width)
        return self._raw_data[start:self._offset]

    async def read_full(self, _min_ms: int) -> bytes:
        start = self._offset
        self._offset = len(self._raw_data)
        return self._raw_data[start:]

    def crop_to(self, milliseconds: int):
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
