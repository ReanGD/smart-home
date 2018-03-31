import utils


class AudioSettings(object):
    def __init__(self, audio: utils.Audio, device_index, channels, sample_format, sample_rate,
                 frames_per_buffer):
        if device_index is not None:
            count = self._audio.get_device_count()
            msg = ("Device index out of range ({} devices available; "
                   "device index should be between 0 and {} inclusive)")
            assert 0 <= device_index < count, msg.format(count, count - 1)

        msg = "Invalid sample_rate: {}"
        assert isinstance(sample_rate, (float, int)) and sample_rate > 0, msg.format(sample_rate)

        self._audio = audio
        self._device_index = device_index
        self._channels = channels
        self._sample_format = sample_format  # size of each sample
        self._sample_rate = sample_rate  # sampling rate in Hertz
        self._frames_per_buffer = frames_per_buffer  # number of frames stored in each buffer

    @property
    def audio(self) -> utils.Audio:
        return self._audio

    @property
    def device_index(self):
        return self._device_index

    @property
    def channels(self):
        return self._channels

    @property
    def sample_format(self):
        return self._sample_format

    @property
    def sample_rate(self):
        return self._sample_rate

    @property
    def frames_per_buffer(self):
        return self._frames_per_buffer
