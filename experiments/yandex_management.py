import config
from logging import getLogger
from nlp import Morphology
from audio import Microphone
from protocols.home_assistant import HASerrializeProtocol, SetDeviceState, entity_to_protobuf
from protocols.transport import TCPClientConnection
from etc import HassTransportConfig, all_entitis


logger = getLogger('demo')


class YandexRecognition(TCPClientConnection):
    def __init__(self):
        super().__init__(logger, HassTransportConfig())
        self._morph = Morphology(all_entitis)
        self._recognizer = config.yandex.create_phrase_recognizer()

    async def start(self, index):
        protocol = HASerrializeProtocol([], logger)
        await self.connect(protocol, max_attempt = -1)

        with Microphone(device_index=index) as mic:
            logger.debug('settings: {}'.format(mic.get_settings()))
            logger.info('start recognize...')
            await self._recognizer.recognize(mic, self.recv_callback)
            logger.info('stop recognize...')

    async def _analyze(self, text):
        cmd = self._morph.analyze(text)
        success = 'place' in cmd and 'device' in cmd and 'device_action' in cmd
        if success:
            logger.info('Found command: {}'.format(cmd))
            device_action = entity_to_protobuf('device_action', cmd['device_action'])
            device = entity_to_protobuf('device', cmd['device'])
            place = entity_to_protobuf('place', cmd['place'])

            msg = SetDeviceState(device_action=device_action,
                                 device=device,
                                 place=place)
            await self.send(msg)

        return success, cmd

    async def recv_callback(self, phrases, is_phrase_finished, _response):
        if not is_phrase_finished:
            text = phrases[0]
            logger.debug(text)
            success, cmd = await self._analyze(text)

            return not success
        else:
            logger.debug('Final result:')
            for text in phrases:
                logger.debug(text)
                await self._analyze(text)

            return False


async def run(index=None):
    try:
        obj = YandexRecognition()
        await obj.start(index)
    except GeneratorExit:
        logger.info('stop record... (KeyboardInterrupt)')
