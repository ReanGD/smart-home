import _portaudio as pa
from .types import paInt16, paFormats


class DeviceInfo(object):
    def __init__(self, default: bool, index: int, name: str, max_input_channels: int,
                 default_sample_rate):
        self.default = default
        self.index = index
        self.name = name
        self.max_input_channels = max_input_channels
        self.default_sample_rate = default_sample_rate


class AudioSettings(object):
    def __init__(self, channels: int, sample_format: int, sample_rate: int):
        if channels is not None:
            assert isinstance(channels, int) and channels >= 1, "A channel must be a positive integer greater than 1"

        if sample_format is not None:
            assert sample_format in paFormats, "Invalid value for sample format"

        if sample_rate is not None:
            msg = "Sample rate (value = {}) must be None or a positive integer".format(sample_rate)
            assert isinstance(sample_rate, (float, int)) and sample_rate > 0, msg

        if sample_rate is not None:
            sample_width = pa.get_sample_size(sample_format)
            msg = "Sample width must be integer between 1 and 4 inclusive"
            assert isinstance(sample_width, int) and 1 <= sample_width <= 4, msg
        else:
            sample_width = None

        self._channels = channels
        self._sample_format = sample_format
        self._sample_rate = sample_rate
        self._sample_width = sample_width

    def clone(self) -> 'AudioSettings':
        return AudioSettings(self.channels, self.sample_format, self.sample_rate)

    @property
    def channels(self) -> [int, None]:
        return self._channels

    @property
    def sample_format(self) -> int:
        # sample farmat: paFloat32, paInt32, paInt24, paInt16, paInt8, paUInt8
        return self._sample_format

    @property
    def sample_rate(self) -> int:
        # sampling rate in Hertz
        return self._sample_rate

    @property
    def sample_width(self) -> int:
        # size of each sample
        return self._sample_width

    def get_duration_ms_by_frames_count(self, count) -> int:
        assert self._sample_rate is not None, "Sample rate is not initialized"
        return int(count * 1000.0 / self._sample_rate)

    def get_frames_count_by_duration_ms(self, ms) -> int:
        assert self._sample_rate is not None, "Sample rate is not initialized"
        return int(ms * self._sample_rate / 1000.0)

    def __str__(self) -> str:
        channels = 'None' if self._channels is None else self._channels
        sample_format = 'None' if self._sample_format is None else paFormats.get(self._sample_format, 'paUnknown')
        sample_rate = 'None' if self._sample_rate is None else self._sample_rate
        sample_width = 'None' if self._sample_width is None else self._sample_width

        msg = 'channels={}, sample_format={}, sample_rate={}, sample_width={}'
        return msg.format(channels, sample_format, sample_rate, sample_width)


class StreamSettings(AudioSettings):
    def __init__(self,
                 device_index: int=None,
                 channels: int=1,
                 sample_format=paInt16,
                 sample_rate: int=None):

        self._device_index = get_device_index(device_index)
        device_info = pa.get_device_info(self._device_index)

        if sample_rate is None:
            sample_rate = device_info.defaultSampleRate
            assert isinstance(sample_rate, (float, int)) and sample_rate > 0, "Invalid default sample rate"

        super().__init__(channels, sample_format, int(sample_rate))

        msg = "Channels should be between 1 and {} inclusive".format(device_info.maxInputChannels)
        assert channels is not None and 0 < channels <= device_info.maxInputChannels, msg

        assert sample_format is not None, "The rate must not be null"

    def clone(self) -> 'StreamSettings':
        return StreamSettings(self.device_index, self.channels, self.sample_format, self.sample_rate)

    @staticmethod
    def get_device_count() -> int:
        return pa.get_device_count()

    @staticmethod
    def get_device_info_by_index(device_index) -> DeviceInfo:
        default_index = pa.get_default_input_device()
        if device_index is None:
            device_index = default_index

        device_info = pa.get_device_info(device_index)

        try:
            device_name = device_info.name.decode('utf-8')
        except UnicodeDecodeError:
            device_name = device_info.name.decode('cp1252')
        default = default_index == device_index

        return DeviceInfo(default, default_index, device_name,
                          device_info.maxInputChannels, device_info.defaultSampleRate)

    @property
    def device_index(self) -> int:
        return self._device_index


def get_device_index(device_index: int) -> int:
    if device_index is not None:
        assert isinstance(device_index, int), "Device index must be None or an integer"
        count = pa.get_device_count()
        msg = ("Device index out of range ({} devices available; "
               "device index should be between 0 and {} inclusive)")
        assert 0 <= device_index < count, msg.format(count, count - 1)
        return device_index
    else:
        return pa.get_default_input_device()
