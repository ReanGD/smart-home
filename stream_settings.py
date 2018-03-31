import audio
import pyaudio


class StreamSettings(object):
    def __init__(self, audio: audio.Audio,
                 device_index: int=None,
                 channels: int=1,
                 sample_format=pyaudio.paInt16,
                 sample_rate: int=None,
                 frames_per_buffer: int=1024):

        if device_index is not None:
            assert isinstance(device_index, int), "Device index must be None or an integer"
            count = self._audio.get_device_count()
            msg = ("Device index out of range ({} devices available; "
                   "device index should be between 0 and {} inclusive)")
            assert 0 <= device_index < count, msg.format(count, count - 1)

        assert isinstance(channels, int) and channels > 0, "Channels must be a positive integer"

        valid_formats = [pyaudio.paFloat32, pyaudio.paInt32, pyaudio.paInt24,
                         pyaudio.paInt16, pyaudio.paInt8, pyaudio.paUInt8]
        assert sample_format in valid_formats, "Invalid value fpr sample format"

        if sample_rate is None:
            device_info = audio.get_device_info_by_index(device_index)
            sample_rate = device_info.get("defaultSampleRate")
            assert isinstance(sample_rate, (float, int)) and sample_rate > 0, \
                "Invalid device info returned from PyAudio: {}".format(device_info)
            sample_rate = int(sample_rate)
        else:
            msg = "Sample rate must be None or a positive integer"
            assert isinstance(sample_rate, int) and sample_rate > 0, msg

        msg = "Chunk size must be a positive integer"
        assert isinstance(frames_per_buffer, int) and frames_per_buffer > 0, msg

        self._audio = audio
        self._device_index = device_index
        self._channels = channels
        self._sample_format = sample_format  # size of each sample
        self._sample_rate = sample_rate  # sampling rate in Hertz
        self._frames_per_buffer = frames_per_buffer  # number of frames stored in each buffer

    def clone(self):
        return StreamSettings(self._audio, self._device_index, self._channels,
                              self._sample_format, self._sample_rate, self._frames_per_buffer)

    @property
    def audio(self) -> audio.Audio:
        return self._audio

    @property
    def device_index(self) -> int:
        return self._device_index

    @property
    def channels(self) -> int:
        return self._channels

    @property
    def sample_format(self):
        return self._sample_format

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    @property
    def frames_per_buffer(self) -> int:
        return self._frames_per_buffer
