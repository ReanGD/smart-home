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


class StreamSettings(object):
    def __init__(self,
                 device_index: int=None,
                 channels: int=1,
                 sample_format=paInt16,
                 sample_rate: int=None):

        device_index = get_device_index(device_index)
        device_info = pa.get_device_info(device_index)
        check_params(device_info, channels, sample_format)

        self._device_index = device_index
        self._channels = channels
        self._sample_format = sample_format
        self._sample_rate = get_sample_rate(device_info, sample_rate)
        self._sample_width = get_sample_width(sample_format)

    def clone(self):
        return StreamSettings(self._device_index, self._channels, self._sample_format,
                              self._sample_rate)

    @staticmethod
    def get_device_count() -> int:
        return pa.get_device_count()

    @staticmethod
    def get_device_info_by_index(device_index):
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

    def get_duration_ms_by_frames_count(self, count):
        return int(count * 1000.0 / self._sample_rate)

    def get_frames_count_by_duration_ms(self, ms):
        return int(ms * self._sample_rate / 1000.0)

    @property
    def device_index(self) -> int:
        return self._device_index

    @property
    def channels(self) -> int:
        return self._channels

    @property
    def sample_format(self):
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

    def __str__(self):
        msg = 'channels={}, sample_format={}, sample_rate={}, sample_width={}'
        return msg.format(self._channels, paFormats.get(self._sample_format, 'paUnknown'),
                          self._sample_rate, self._sample_width)


def get_device_index(device_index):
    if device_index is not None:
        assert isinstance(device_index, int), "Device index must be None or an integer"
        count = pa.get_device_count()
        msg = ("Device index out of range ({} devices available; "
               "device index should be between 0 and {} inclusive)")
        assert 0 <= device_index < count, msg.format(count, count - 1)
        return device_index
    else:
        return pa.get_default_input_device()


def check_params(device_info, channels, sample_format):
    msg = ("Channels must be a positive integer. "
           "Channels should be between 1 and {} inclusive").format(device_info.maxInputChannels)
    assert isinstance(channels, int) and 0 < channels <= device_info.maxInputChannels, msg

    assert sample_format in paFormats, "Invalid value for sample format"


def get_sample_width(sample_format):
    sample_width = pa.get_sample_size(sample_format)
    msg = "Sample width must be integer between 1 and 4 inclusive"
    assert isinstance(sample_width, int) and 1 <= sample_width <= 4, msg

    return sample_width


def get_sample_rate(device_info, sample_rate):
    if sample_rate is None:
        sample_rate = device_info.defaultSampleRate
        msg = "Invalid device info returned from PyAudio"
        assert isinstance(sample_rate, (float, int)) and sample_rate > 0, msg
    else:
        msg = "Sample rate must be None or a positive integer"
        assert isinstance(sample_rate, int) and sample_rate > 0, msg

    return int(sample_rate)
