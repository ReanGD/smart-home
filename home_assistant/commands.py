from logging import Logger
from typing import Optional
from homeassistant.core import HomeAssistant
from nlp import Morphology
from etc import all_entitis


class HassCommands:
    def __init__(self, logger: Logger, hass: HomeAssistant, default_place: str):
        self._hass = hass
        self._logger = logger
        self._morph = Morphology(all_entitis)
        self._default_place = default_place

    def _check_device(self, device: Optional[str]) -> bool:
        if device is None:
            self._logger.error('Unknown "device": None')
            return False

        if device not in ['light', 'tv', 'music']:
            self._logger.error('Unknown "device": {}'.format(device))
            return False

        if device != 'light':
            self._logger.error('Unsupported "device": {}'.format(device))
            return False

        return True

    def _check_device_action(self, device_action: Optional[str]) -> bool:
        if device_action is None:
            self._logger.error('Unknown "device_action": None')
            return False

        if device_action not in ['turn_off', 'turn_on']:
            self._logger.error('Unknown "device_action": {}'.format(device_action))
            return False

        return True

    def _check_place(self, place: Optional[str]):
        if place is None:
            self._logger.error('Unknown "place": None')
            return False

        if place not in ['hall', 'kitchen', 'restroom', 'bathroom', 'livingroom', 'playroom',
                         'all', 'here']:
            self._logger.error('Unknown "place": {}'.format(place))
            return False

        return True

    def _make_name(self, device: str, device_action: str, place: str) -> str:
        if device_action == 'turn_off':
            device_action_str = 'off'
        else:
            device_action_str = 'on'

        if place == 'here':
            place_str = self._default_place
        else:
            place_str = place

        result = '{}_{}_{}'.format(place_str, device, device_action_str)
        return result

    async def execute(self, message: str) -> bool:
        cmd = self._morph.analyze(message)

        device = cmd.get('device', None)
        device_action = cmd.get('device_action', None)
        place = cmd.get('place', None)

        if not self._check_device(device):
            return False

        if not self._check_device_action(device_action):
            return False

        if not self._check_place(place):
            return False

        service_data = {}
        name = self._make_name(device, device_action, place)
        self._logger.debug("Call script.{}".format(name))
        await self._hass.services.async_call('script', name, service_data, False)

        return True
