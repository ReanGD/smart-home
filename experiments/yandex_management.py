import config
from logging import getLogger
from audio import Microphone
from protocols.home_assistant import HASerrializeProtocol, UserTextCommand, UserTextCommandResult
from protocols.transport import TCPClientConnection
from etc import HassTransportConfig


logger = getLogger('demo')


class YandexRecognition(TCPClientConnection):
    def __init__(self):
        super().__init__(logger, HassTransportConfig())
        self._recognizer = config.yandex.create_phrase_recognizer()
        self._isFinished = False

    async def start(self, index):
        protocol = HASerrializeProtocol([UserTextCommandResult], logger)
        await self.connect(protocol, max_attempt = -1)

        with Microphone(device_index=index) as mic:
            logger.debug('settings: {}'.format(mic.get_settings()))
            logger.info('start recognize...')
            self._isFinished = False
            await self._recognizer.recognize(mic, self.recv_callback)
            logger.info('stop recognize...')

    async def on_user_text_command_result(self, message: UserTextCommandResult):
        if message.isFinished:
            self._isFinished = True

    async def recv_callback(self, phrases, is_phrase_finished, _response):
        if self._isFinished:
            return False

        if not is_phrase_finished:
            text = phrases[0]
            logger.debug(text)
            await self.send(UserTextCommand(text=text))

            return True
        else:
            logger.debug('Final result:')
            for text in phrases:
                logger.debug(text)
                await self.send(UserTextCommand(text=text))

            return False


async def run(index=None):
    try:
        obj = YandexRecognition()
        await obj.start(index)
    except GeneratorExit:
        logger.info('stop record... (KeyboardInterrupt)')
