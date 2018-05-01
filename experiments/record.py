import audio


def run():
    device = audio.Device()
    settings = audio.StreamSettings(device, device_index=None)
    data = []
    try:
        print("settings: {}".format(settings))
        mic = device.create_microphone_stream(settings)
        print("start record...")

        while True:
            data.append(mic.read(settings.frames_per_buffer))

    except KeyboardInterrupt:
        print("stop record...")
        audio.AudioData(b''.join(data), settings).save_as_wav("record.wav")
    finally:
        device.terminate()
