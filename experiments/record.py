from audio import Microphone, Storage


async def run(index=None):
    mic = Storage(Microphone(index))
    print("settings: {}".format(mic.get_settings()))
    print("start record...")

    try:
        while True:
            await mic.read(50)
    except GeneratorExit:
        print("stop record...")
        mic.save_as_wav("record.wav")
    finally:
        mic.close()
