from audio import StreamSettings, Microphone, AudioData


async def run(index=None):
    settings = StreamSettings(device_index=index)
    print("settings: {}".format(settings))
    data = AudioData(b'', settings)
    try:
        with Microphone(settings) as mic:
            print("start record...")
            while True:
                data.add_raw_data(await mic.read(50))
    except GeneratorExit:
        print("stop record...")
        data.save_as_wav("record.wav")
