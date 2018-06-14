from pyaudio import paFloat32, paInt32, paInt24, paInt16, paInt8, paUInt8, get_sample_size


formats = {paFloat32: "paFloat32",
           paInt32: "paInt32",
           paInt24: "paInt24",
           paInt16: "paInt16",
           paInt8: "paInt8",
           paUInt8: "paUInt8"}


class StreamSettings(object):
    def __init__(self, device,
                 device_index: int=None,
                 channels: int=1,
                 sample_format=paInt16,
                 sample_rate: int=None,
                 frames_per_buffer: int=1024):

        if device_index is not None:
            assert isinstance(device_index, int), "Device index must be None or an integer"
            count = device.get_device_count()
            msg = ("Device index out of range ({} devices available; "
                   "device index should be between 0 and {} inclusive)")
            assert 0 <= device_index < count, msg.format(count, count - 1)

        assert isinstance(channels, int) and channels > 0, "Channels must be a positive integer"
        assert sample_format in formats, "Invalid value fpr sample format"

        if sample_rate is None:
            device_info = device.get_device_info_by_index(device_index)
            sample_rate = device_info.get("defaultSampleRate")
            assert isinstance(sample_rate, (float, int)) and sample_rate > 0, \
                "Invalid device info returned from PyAudio: {}".format(device_info)
            sample_rate = int(sample_rate)
        else:
            msg = "Sample rate must be None or a positive integer"
            assert isinstance(sample_rate, int) and sample_rate > 0, msg

        msg = "Chunk size must be a positive integer"
        assert isinstance(frames_per_buffer, int) and frames_per_buffer > 0, msg

        sample_width = get_sample_size(sample_format)
        msg = "Sample width must be integer between 1 and 4 inclusive"
        assert isinstance(sample_width, int) and 1 <= sample_width <= 4, msg

        self._device = device
        self._device_index = device_index
        self._channels = channels
        self._sample_format = sample_format
        self._sample_rate = sample_rate
        self._sample_width = sample_width
        self._frames_per_buffer = frames_per_buffer

    def clone(self):
        return StreamSettings(self._device, self._device_index, self._channels,
                              self._sample_format, self._sample_rate, self._frames_per_buffer)

    def get_duration_ms_by_frames_count(self, count):
        return int(count * 1000.0 / self._sample_rate)

    def get_frames_count_by_duration_ms(self, ms):
        return int(ms * self._sample_rate / 1000.0)

    @property
    def device(self):
        return self._device

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

    @property
    def frames_per_buffer(self) -> int:
        # length of the audio buffer in frames
        return self._frames_per_buffer

    def __str__(self):
        msg = 'channels={}, sample_format={}, sample_rate={}, sample_width={}, frames_per_buffer={}'
        return msg.format(self._channels, formats[self._sample_format], self._sample_rate,
                          self._sample_width, self._frames_per_buffer)
