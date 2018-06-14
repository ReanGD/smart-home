import audio


def run(index=None):
    settings = audio.StreamSettings(device_index=index)
    mic = None
    data = []
    try:
        print("settings: {}".format(settings))
        mic = audio.Microphone(settings)
        print("start record...")

        while True:
            data.append(mic.read(settings.frames_per_buffer))

    except KeyboardInterrupt:
        print("stop record...")
        audio.AudioData(b''.join(data), settings).save_as_wav("record.wav")
    finally:
        if mic is not None:
            mic.close()
