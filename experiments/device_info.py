import audio


def run():
    device = audio.Device()
    try:
        template = '{}: "{}", maxInputChannels: {}, defaultSampleRate: {}'
        default_ind = device.get_device_info_by_index(None)['index']

        for ind in range(device.get_device_count()):
            info = device.get_device_info_by_index(ind)

            index = info['index']
            name = info['name']
            max_input_channels = info['maxInputChannels']

            if max_input_channels == 0:
                continue

            if default_ind == index:
                name = '(default) ' + name

            print(template.format(index, name, max_input_channels, info['defaultSampleRate']))

    finally:
        device.terminate()