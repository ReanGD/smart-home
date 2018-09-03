import config
import asyncio
from nlp import Morphology
from etc import all_entitis
from logging import getLogger
from audio import StreamSettings, Microphone
from protocols.transport import TCPConnection, create_client
from protocols.home_assistant import (HASerrializeProtocol, StartRecognition, SetDeviceState,
                                      entity_to_protobuf)


logger = getLogger('demo')


class HomeAssistentHandler(object):
    def __init__(self, event):
        self._event = event

    async def on_connect(self, conn: TCPConnection):
        pass

    async def on_start_recognition(self, conn: TCPConnection, message: StartRecognition):
        self._event.set()


class Demo(object):
    def __init__(self, index):
        self._morph = Morphology(all_entitis)
        self._settings = StreamSettings(device_index=index)
        self._recognizer = config.yandex.create_phrase_recognizer()
        self._start_recognition_event = asyncio.Event()
        self._client = None
        logger.debug('settings: {}'.format(self._settings))

    def handler_factory(self):
        return HomeAssistentHandler(self._start_recognition_event)

    async def run(self):
        protocol = HASerrializeProtocol([StartRecognition], logger)
        self._client = await create_client('192.168.1.20', 8083, self.handler_factory, protocol,
                                           logger)

        with Microphone(self._settings) as mic:
            while True:
                await self._start_recognition_event.wait()
                logger.info('start recognize...')
                await self._recognizer.recognize(mic, self.recv_callback)
                self._start_recognition_event.clear()
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
            await self._client.send(msg)

        return success, cmd

    async def recv_callback(self, phrases, is_phrase_finished, response):
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
        obj = Demo(index)
        await obj.run()
    except GeneratorExit:
        logger.info('stop record... (KeyboardInterrupt)')
