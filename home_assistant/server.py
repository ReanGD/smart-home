from logging import Logger, getLogger
from homeassistant.core import HomeAssistant
from nlp import Morphology
from etc import HassTransportConfig, all_entitis
from protocols.transport import TCPServerConnection, TCPServer
from protocols.home_assistant import (HASerrializeProtocol, StartRecognition,
                                      UserTextCommand, UserTextCommandResult)


class HomeAssistentConnection(TCPServerConnection):
    def __init__(self, logger: Logger, hass: HomeAssistant):
        super().__init__(logger)
        self._hass = hass
        self._morph = Morphology(all_entitis)

    async def _run_command(self, cmd):
        self._logger.info('Recognized the command: {}'.format(cmd))

        device_action = cmd['device_action']
        device = cmd['device']
        place = cmd['place']

        if device not in ['light', 'tv', 'music']:
            self._logger.error('Unknown "device": {}'.format(device))
            return False

        if device != 'light':
            self._logger.error('Unsupported "device": {}'.format(device))
            return False

        if device_action not in ['turn_off', 'turn_on']:
            self._logger.error('Unknown "device_action": {}'.format(device_action))
            return False

        if device_action == 'turn_off':
            device_action_str = 'off'
        else:
            device_action_str = 'on'

        if place not in ['hall', 'kitchen', 'restroom', 'bathroom', 'livingroom', 'playroom',
                         'all', 'here']:
            self._logger.error('Unknown "place": {} for "device_action": {}'.format(
                place, device_action))
            return False

        if place == 'here':
            place_str = 'livingroom'
        else:
            place_str = place

        service = '{}_{}_{}'.format(place_str, device, device_action_str)
        service_data = {}
        await self._hass.services.async_call('script', service, service_data, False)

        return True

    async def on_user_text_command(self, message: UserTextCommand):
        cmd = self._morph.analyze(message.text)
        isFinished = 'place' in cmd and 'device' in cmd and 'device_action' in cmd
        if isFinished:
            isFinished = await self._run_command(cmd)

        await self.send(UserTextCommandResult(isFinished=isFinished))


class HomeAssistentServer(object):
    def __init__(self, domain: str, hass: HomeAssistant):
        self._hass = hass
        self._domain = domain
        self._logger = getLogger(domain)
        self._server = TCPServer(self._logger, HassTransportConfig())

    # async def activate_handle(self, call):
    #     await self._server.send_to_all(StartRecognition())

    async def run(self, domain: str):
        protocol = HASerrializeProtocol([UserTextCommand], self._logger)

        def handler_factory(logger):
            return HomeAssistentConnection(logger, self._hass)

        await self._server.run(handler_factory, protocol)
        # self._hass.services.async_register(domain, 'activate', self.activate_handle)


async def run(domain: str, hass: HomeAssistant, config) -> bool:
    # activate_timeout = config['voice_commands'].get('activate_timeout', 10)
    server = HomeAssistentServer(domain, hass)
    await server.run(domain)

    return True
