import config
from audio import StreamSettings, Microphone


async def run(index=None):
    settings = StreamSettings(device_index=index)
    recognizer = config.yandex_protobuf.create_phrase_recognizer()
    print("settings: {}".format(settings))

    try:
        await recognizer.recognize_start(settings)
        with Microphone(settings) as mic:
            print("start record...")
            while True:
                await recognizer.recognize_add_frames(await mic.read(50))
    except GeneratorExit:
        print("stop record...")
    finally:
        recognizer.recognize_finish()
        recognizer.close()
