import config
import asyncio
from npl import Morphology
from etc import all_entitis
from logging import getLogger
from audio import StreamSettings, Microphone
from protocols.transport import ProtoConnection, create_client
from protocols.home_assistant import (HASerrializeProtocol, StartRecognition, SetDeviceState,
                                      entity_to_protobuf)


logger = getLogger('demo')


class HomeAssistentHandler(object):
    def __init__(self):
        pass

    async def on_connect(self):
        pass

    async def on_StartRecognition(self, conn: ProtoConnection, message: StartRecognition):
        pass


class Demo(object):
    def __init__(self, index):
        self._morph = Morphology(all_entitis)
        self._settings = StreamSettings(device_index=index)
        self._recognizer = config.yandex.create_phrase_recognizer()
        self._client_future = asyncio.ensure_future(self.create_client())
        self._client = None
        logger.debug('settings: {}'.format(self._settings))

    async def create_client(self):
        protocol = HASerrializeProtocol([StartRecognition], logger)
        return await create_client('127.0.0.1', 8083, HomeAssistentHandler, protocol, logger)

    async def run(self):
        with Microphone(self._settings) as mic:
            logger.info('start record...')
            await self._recognizer.recognize(mic, self.recv_callback)
            logger.info('stop record...')

    async def _analyze(self, text):
        cmd = self._morph.analyze(text)
        success = 'place' in cmd and 'device' in cmd and 'device_action' in cmd
        if success:
            logger.info('Found command: {}'.format(cmd))
            if self._client is None:
                asyncio.wait(self._client_future)
                self._client = self._client_future.result()

                device_action = entity_to_protobuf('device_action', cmd['device_action'])
                device = entity_to_protobuf('device', cmd['device'])
                place = entity_to_protobuf('place', cmd['place'])

                msg = SetDeviceState(device_action=device_action,
                                     device=device,
                                     place=place)
                await self._client.send_protobuf(msg)

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
