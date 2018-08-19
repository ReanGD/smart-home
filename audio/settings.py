import _portaudio as pa
from .types import paInt16, paFormats


class AudioSettings(object):
    def __init__(self, channels: int=1,
                 sample_format: int=paInt16,
                 sample_rate: int=0):
        msg = 'Param "channels" ({}) must be a positive integer greater than 1'.format(channels)
        assert channels is not None and isinstance(channels, int) and 0 < channels, msg

        if sample_format not in paFormats:
            formats = ', '.join([str(it) for it in paFormats.keys()])
            msg = 'Param "sample_format" ({}) must be one of: [{}]'.format(sample_format, formats)
            assert sample_format in paFormats, msg

        msg = 'Param "sample_rate" ({}) must be a positive integer'.format(sample_rate)
        assert sample_rate is not None and isinstance(sample_rate, (float, int)) and sample_rate > 0, msg

        sample_width = pa.get_sample_size(sample_format)
        msg = 'Value "sample_width" ({}) must be integer between 1 and 4 inclusive'.format(sample_width)
        assert isinstance(sample_width, int) and 1 <= sample_width <= 4, msg

        self._channels = channels
        self._sample_format = sample_format
        self._sample_rate = int(sample_rate)
        self._sample_width = sample_width

    def clone(self) -> 'AudioSettings':
        return AudioSettings(self.channels, self.sample_format, self.sample_rate)

    @property
    def channels(self) -> int:
        return self._channels

    @property
    def sample_format(self) -> int:
        # sample farmat: paInt32, paInt24, paInt16, paUInt8
        return self._sample_format

    @property
    def sample_rate(self) -> int:
        # sampling rate in Hertz
        return self._sample_rate

    @property
    def sample_width(self) -> int:
        # size of each sample in bytes
        return self._sample_width

    def get_duration_ms_by_frames_count(self, count) -> int:
        return int(count * 1000.0 / self._sample_rate)

    def get_frames_count_by_duration_ms(self, ms) -> int:
        return int(ms * self._sample_rate / 1000.0)

    def __str__(self) -> str:
        msg = 'channels={}, sample_format={}, sample_rate={}, sample_width={}'
        return msg.format(self._channels, paFormats.get(self._sample_format, 'paUnknown'),
                          self._sample_rate, self._sample_width)
