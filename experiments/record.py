from audio import StreamSettings, Microphone, AudioData


def run(index=None):
    settings = StreamSettings(device_index=index)
    data = []
    try:
        print("settings: {}".format(settings))
        with Microphone(settings) as mic:
            print("start record...")
            while True:
                data.append(mic.read(50))
    except KeyboardInterrupt:
        print("stop record...")
        AudioData(b''.join(data), settings).save_as_wav("record.wav")
