import audio


def run():
    device = audio.Device()
    try:
        for ind in range(device.get_device_count()):
            print(device.get_device_info_by_index(ind))
            print()
    finally:
        device.terminate()