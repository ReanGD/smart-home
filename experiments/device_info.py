import audio


async def run():
    for ind in range(audio.Devices.get_device_count()):
        info = audio.Devices.get_device_info_by_index(ind)
        if info.max_input_channels != 0:
            print(info)
