import config
from audio import StreamSettings, Microphone
from npl import Morphology
from etc import all_entitis


class Demo(object):
    def __init__(self, index):
        self._morph = Morphology(all_entitis)
        self._settings = StreamSettings(device_index=index)
        self._recognizer = config.yandex.create_phrase_recognizer()
        print("settings: {}".format(self._settings))

    async def run(self):
        with Microphone(self._settings) as mic:
            print("start record...")
            await self._recognizer.recognize(mic, self.recv_callback)
            print("stop record...")

    def _analyze(self, text):
        cmd = self._morph.analyze(text)
        success = 'room' in cmd and 'room_device' in cmd and 'room_device_action' in cmd
        if success:
            print('Found command: {}'.format(cmd))

        return success, cmd

    async def recv_callback(self, phrases, is_phrase_finished, response):
        if not is_phrase_finished:
            text = phrases[0]
            print(text)
            success, cmd = self._analyze(text)

            return not success
        else:
            print('Final result:')
            for text in phrases:
                print(text)
                self._analyze(text)

            return False


async def run(index=None):
    try:
        obj = Demo(index)
        await obj.run()
    except GeneratorExit:
        print("stop record... (KeyboardInterrupt)")
