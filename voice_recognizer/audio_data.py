import io
import wave
import pyaudio
import audioop
from voice_recognizer.stream_settings import StreamSettings


class AudioData(object):
    def __init__(self, raw_data, in_settings: StreamSettings):
        self._raw_data = raw_data
        self._in_settings = in_settings

    def add_raw_data(self, raw_data):
        self._raw_data += raw_data

    def get_raw_data(self, out_settings: StreamSettings=None):
        if out_settings is None:
            return self._raw_data

        in_sample_rate = self._in_settings.sample_rate
        out_sample_rate = out_settings.sample_rate
        in_sample_width = self._in_settings.sample_width
        out_sample_width = out_settings.sample_width

        raw_data = self._raw_data

        # make sure unsigned 8-bit audio (which uses unsigned samples)
        # is handled like higher sample width audio (which uses signed samples)
        if in_sample_width == 1:
            # subtract 128 from every sample to make them act like signed samples
            raw_data = audioop.bias(raw_data, 1, -128)

        if in_sample_rate != out_sample_rate:
            raw_data, _ = audioop.ratecv(raw_data, in_sample_width,
                                         self._in_settings.channels, in_sample_rate,
                                         out_sample_rate, None)

        if in_sample_width != out_sample_width:
            # we're converting the audio into 24-bit
            # workaround for https://bugs.python.org/issue12866
            if out_sample_width == 3:
                # convert audio into 32-bit first, which is always supported
                raw_data = audioop.lin2lin(raw_data, in_sample_width, 4)
                try:
                    # test whether 24-bit audio is supported
                    # for example, ``audioop`` in Python 3.3 and below don't support
                    # sample width 3, while Python 3.4+ do
                    audioop.bias(b"", 3, 0)
                except audioop.error:
                    # this version of audioop doesn't support 24-bit audio
                    # (probably Python 3.3 or less)
                    #
                    # since we're in little endian,
                    # we discard the first byte from each 32-bit sample to get a 24-bit sample
                    raw_data = b"".join(raw_data[i + 1:i + 4] for i in range(0, len(raw_data), 4))
                else:
                    # 24-bit audio fully supported, we don't need to shim anything
                    raw_data = audioop.lin2lin(raw_data, in_sample_width, out_sample_width)
            else:
                raw_data = audioop.lin2lin(raw_data, in_sample_width, out_sample_width)

        # if the output is 8-bit audio with unsigned samples,
        # convert the samples we've been treating as signed to unsigned again
        if out_sample_width == 1:
            # add 128 to every sample to make them act like unsigned samples again
            raw_data = audioop.bias(raw_data, 1, 128)

        return raw_data

    def get_settings(self) -> StreamSettings:
        return self._in_settings

    @staticmethod
    def load_as_wav(file, out_settings: StreamSettings):
        wav_reader = wave.open(file, "rb")
        try:
            sample_format = pyaudio.get_format_from_width(wav_reader.getsampwidth())
            in_settings = StreamSettings(out_settings.device,
                                         channels = wav_reader.getnchannels(),
                                         sample_rate = wav_reader.getframerate(),
                                         sample_format = sample_format)
            raw_data = wav_reader.readframes(wav_reader.getnframes())
            raw_data = AudioData(raw_data, in_settings).get_raw_data(out_settings)
            return AudioData(raw_data, out_settings)
        finally:
            wav_reader.close()

    def save_as_wav(self, file, out_settings: StreamSettings = None):
        settings = out_settings if out_settings is not None else self._in_settings

        wav_writer = wave.open(file, "wb")
        try:
            wav_writer.setnchannels(settings.channels)
            wav_writer.setsampwidth(settings.sample_width)
            wav_writer.setframerate(settings.sample_rate)
            wav_writer.writeframes(self.get_raw_data(out_settings))
        finally:
            wav_writer.close()

    def get_wav_data(self, out_settings: StreamSettings=None):
        file = io.BytesIO()
        self.save_as_wav(file, out_settings)
        return file.getvalue()
