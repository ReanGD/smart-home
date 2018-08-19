import config
from logging import getLogger
from audio import Microphone


logger = getLogger('demo')


class YandexRecognition(object):
    def __init__(self):
        self._recognizer = config.yandex.create_phrase_recognizer()

    async def run(self, index):
        with Microphone(device_index=index) as mic:
            logger.debug('settings: {}'.format(mic.get_settings()))
            while True:
                logger.info('start recognize...')
                await self._recognizer.recognize(mic, self.recv_callback)
                logger.info('stop recognize...')

    async def recv_callback(self, phrases, is_phrase_finished, response):
        if not is_phrase_finished:
            logger.debug(phrases[0])
        else:
            logger.debug('Final result:')
            for text in phrases:
                logger.debug(text)

        return not is_phrase_finished


async def run(index=None):
    try:
        obj = YandexRecognition()
        await obj.run(index)
    except GeneratorExit:
        logger.info('stop record... (KeyboardInterrupt)')
