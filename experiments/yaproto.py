import config
from audio import StreamSettings, Microphone


async def recv_callback(phrases, is_phrase_finished, response):
    if is_phrase_finished:
        print('Final result:')
        for it in phrases:
            print(it)
        return False
    else:
        print(phrases[0])
        return True


async def run(index=None):
    try:
        settings = StreamSettings(device_index=index)
        recognizer = config.yandex.create_phrase_recognizer()
        print("settings: {}".format(settings))
        with Microphone(settings) as mic:
            print("start record...")
            await recognizer.recognize(mic, recv_callback)
            print("stop record...")
    except GeneratorExit:
        print("stop record... (KeyboardInterrupt)")

