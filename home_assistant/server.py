import asyncio
from protocols.transport import ProtoConnection, create_server, create_client
from protocols.home_assistant import HASerrializeProtocol, SetDeviceState

import logging
from sys import stdout
import homeassistant.components.switch as switch


log_handler = logging.StreamHandler(stdout)
log_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s'))
logger = logging.getLogger('demo')
logger.setLevel(logging.DEBUG)
logger.addHandler(log_handler)


class HomeAssistentHandler(object):
    def __init__(self, hass):
        self._hass = hass

    async def on_connect(self):
        pass

    async def on_SetDeviceState(self, conn: ProtoConnection, message: SetDeviceState):
        logger.error('on handle')
        switch.async_turn_off(self._hass, 'switch.hall_switch_right_ceiling_light')


async def run(hass):
    def handler_factory():
        return HomeAssistentHandler(hass)

    protocol = HASerrializeProtocol([SetDeviceState], logger)
    await create_server('127.0.0.1', 8083, handler_factory, protocol, logger)
