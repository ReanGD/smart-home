import audio


def run():
    seconds = 15

    device = audio.Device()
    try:
        settings = audio.StreamSettings(device, device_index=None)
        print("settings: {}".format(settings))
        mic = device.create_microphone_stream(settings)

        step_cnt = int(settings.sample_rate / settings.frames_per_buffer * seconds)
        print("start record...")
        data = b''.join([mic.read(settings.frames_per_buffer) for _ in range(step_cnt)])
        print("stop record...")

        audio.AudioData(data, settings).save_as_wav("record.wav")
    finally:
        device.terminate()