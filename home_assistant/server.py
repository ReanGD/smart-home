from logging import Logger, getLogger
from homeassistant.components import switch
from homeassistant.core import HomeAssistant
from nlp import Morphology
from etc import HassTransportConfig, all_entitis
from protocols.transport import TCPServerConnection, TCPServer
from protocols.home_assistant import (HASerrializeProtocol, StartRecognition,
                                      UserTextCommand, UserTextCommandResult)

_TURN_ON_LIGHT_PLACE_TO_IDS = {
    'hall': ['switch.hall_light_ceiling'],
    'kitchen': ['switch.kitchen_light_ceiling'],
    'restroom': ['switch.restroom_light_ceiling'],
    'bathroom': ['switch.bathroom_light_ceiling'],
    'livingroom': ['switch.livingroom_light_ceiling'],
    'playroom': ['switch.playroom_light_ceiling'],
}

_TURN_ON_LIGHT_PLACE_TO_IDS['here'] = _TURN_ON_LIGHT_PLACE_TO_IDS['livingroom']

_TURN_ON_LIGHT_PLACE_TO_IDS['all'] = (
    _TURN_ON_LIGHT_PLACE_TO_IDS['hall'] +
    _TURN_ON_LIGHT_PLACE_TO_IDS['kitchen'] +
    _TURN_ON_LIGHT_PLACE_TO_IDS['restroom'] +
    _TURN_ON_LIGHT_PLACE_TO_IDS['bathroom'] +
    _TURN_ON_LIGHT_PLACE_TO_IDS['livingroom'] +
    _TURN_ON_LIGHT_PLACE_TO_IDS['playroom'])

_TURN_OFF_LIGHT_PLACE_TO_IDS = {
    'hall': ['switch.hall_light_ceiling'],
    'kitchen': ['switch.kitchen_light_ceiling',
                'switch.kitchen_light_backlight'],
    'restroom': ['switch.restroom_light_ceiling'],
    'bathroom': ['switch.bathroom_light_ceiling',
                 'switch.bathroom_light_ceiling_additional'],
    'livingroom': ['switch.livingroom_light_ceiling'],
    'playroom': ['switch.playroom_light_ceiling'],
}

_TURN_OFF_LIGHT_PLACE_TO_IDS['here'] = _TURN_OFF_LIGHT_PLACE_TO_IDS['livingroom']

_TURN_OFF_LIGHT_PLACE_TO_IDS['all'] = (
    _TURN_OFF_LIGHT_PLACE_TO_IDS['hall'] +
    _TURN_OFF_LIGHT_PLACE_TO_IDS['kitchen'] +
    _TURN_OFF_LIGHT_PLACE_TO_IDS['restroom'] +
    _TURN_OFF_LIGHT_PLACE_TO_IDS['bathroom'] +
    _TURN_OFF_LIGHT_PLACE_TO_IDS['livingroom'] +
    _TURN_OFF_LIGHT_PLACE_TO_IDS['playroom'])

_DEVICE_ACTION_TO_FUNC = {
    'turn_off': (switch.async_turn_off, _TURN_ON_LIGHT_PLACE_TO_IDS),
    'turn_on':  (switch.async_turn_on, _TURN_OFF_LIGHT_PLACE_TO_IDS),
}


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

        func, device_map = _DEVICE_ACTION_TO_FUNC.get(device_action, (None, None))
        if func is None:
            self._logger.error('Unknown "device_action": {}'.format(device_action))
            return False

        device_ids = device_map.get(place, None)
        if device_ids is None:
            self._logger.error('Unknown "place": {} for "device_action": {}'.format(
                place, device_action))
            return False

        for device_id in device_ids:
            func(self._hass, device_id)

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
