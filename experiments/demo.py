import config
import asyncio
from npl import Morphology
from etc import all_entitis
from logging import getLogger
from audio import StreamSettings, Microphone
from protocols.transport import ProtoConnection, create_client
from protocols.home_assistant import HASerrializeProtocol, StartRecognition, SetDeviceState


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

                #   enum DeviceAction {
                #     TurnOff = 0;
                #     TurnOn = 1;
                #   }

                if cmd['device_action'] == 'turn_off':
                    device_action = 0
                elif cmd['device_action'] == 'turn_on':
                    device_action = 1
                else:
                    raise RuntimeError('unknown device_action = {}'.format(cmd['device_action']))

                #   enum Device {
                #     Light = 0;
                #     TV = 1;
                #     Music = 2;
                #   }
                if cmd['device'] == 'light':
                    device = 0
                else:
                    logger.info('Unsaported device: {}'.format(cmd['device']))
                    return

                #   enum Place {
                #     All = 0;
                #     Here = 1;
                #     Hall = 2;
                #     Kitchen = 3;
                #     Toilet = 4;
                #     Bathroom = 5;
                #     Livingroom = 6;
                #     Playroom = 7;
                #   }

                if cmd['place'] == 'all':
                    place = 0
                elif cmd['place'] == 'here':
                    place = 1
                elif cmd['place'] == 'hall':
                    place = 2
                elif cmd['place'] == 'kitchen':
                    place = 3
                elif cmd['place'] == 'toilet':
                    place = 4
                elif cmd['place'] == 'bathroom':
                    place = 5
                elif cmd['place'] == 'livingroom':
                    place = 6
                elif cmd['place'] == 'playroom':
                    place = 7
                else:
                    raise RuntimeError('unknown place = {}'.format(cmd['place']))

                msg = SetDeviceState(device_action=device_action, device=device, place=place)
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
