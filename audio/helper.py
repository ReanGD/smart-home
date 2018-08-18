import audioop
from .settings import AudioSettings


def audio_data_converter(raw_data, in_settings: AudioSettings, out_settings: AudioSettings):
    def fill(param1, param2, name):
        if param1 is None:
            param1 = param2
        elif param2 is None:
            param2 = param1

        if param1 is None:
            msg = 'It is not possible to convert audio data. Parameter "{}" is not specified'
            raise RuntimeError(msg.format(name))
        else:
            return param1, param2

    in_sample_rate, out_sample_rate = fill(in_settings.sample_rate, out_settings.sample_rate, 'Sample rate')
    in_sample_width, out_sample_width = fill(in_settings.sample_width, out_settings.sample_width, 'Sample format')
    in_channels, out_channels = fill(in_settings.channels, out_settings.channels, 'Channels')

    if in_channels != out_channels:
        raise RuntimeError('Can not convert audio data. The number of channels must be the same.')

    if in_sample_rate == out_sample_rate and in_sample_width == out_sample_width:
        return raw_data

    # make sure unsigned 8-bit audio (which uses unsigned samples)
    # is handled like higher sample width audio (which uses signed samples)
    if in_sample_width == 1:
        # subtract 128 from every sample to make them act like signed samples
        raw_data = audioop.bias(raw_data, 1, -128)

    if in_sample_rate != out_sample_rate:
        raw_data, _ = audioop.ratecv(raw_data, in_sample_width, in_channels, in_sample_rate, out_sample_rate, None)

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
