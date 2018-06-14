import audio


def run():
    tmpl = '{}: "{}", maxInputChannels: {}, defaultSampleRate: {}'
    for ind in range(audio.StreamSettings.get_device_count()):
        info = audio.StreamSettings.get_device_info_by_index(ind)
        if info.max_input_channels == 0:
            continue

        if info.default:
            info.name = '(default) ' + info.name
        print(tmpl.format(ind, info.name, info.max_input_channels, info.default_sample_rate))
