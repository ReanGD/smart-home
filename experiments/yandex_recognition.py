import config
from npl import Morphology
from etc import all_entitis
from logging import getLogger
from audio import StreamSettings, Microphone


logger = getLogger('demo')


class YandexRecognition(object):
    def __init__(self, index):
        self._morph = Morphology(all_entitis)

        from audio.types import paInt32
        self._settings = StreamSettings(device_index=index)
        self._recognizer = config.yandex.create_phrase_recognizer()
        logger.debug('settings: {}'.format(self._settings))

    async def run(self):
        with Microphone(self._settings) as mic:
            while True:
                logger.info('start recognize...')
                await self._recognizer.recognize(mic, self.recv_callback)
                logger.info('stop recognize...')

    async def _analyze(self, text):
        cmd = self._morph.analyze(text)
        success = 'place' in cmd and 'device' in cmd and 'device_action' in cmd
        if success:
            logger.info('Found command: {}'.format(cmd))

        return success

    async def recv_callback(self, phrases, is_phrase_finished, response):
        if not is_phrase_finished:
            text = phrases[0]
            logger.debug(text)
            success = await self._analyze(text)

            return not success
        else:
            logger.debug('Final result:')
            for text in phrases:
                logger.debug(text)
                await self._analyze(text)

            return False


async def run(index=None):
    try:
        obj = YandexRecognition(index)
        await obj.run()
    except GeneratorExit:
        logger.info('stop record... (KeyboardInterrupt)')
