import logging
from protocols.transport import ProtoConnection, create_server
from protocols.home_assistant import (HASerrializeProtocol, StartRecognition, SetDeviceState,
                                      protobuf_to_device_id)
import homeassistant.components.switch as switch


logger = logging.getLogger('homeassistant.core')


class HomeAssistentHandler(object):
    def __init__(self, hass):
        self._hass = hass

    async def on_connect(self):
        pass

    async def on_SetDeviceState(self, conn: ProtoConnection, message: SetDeviceState):
        ids = protobuf_to_device_id(message.device, message.place, message.device_action)
        for device_id in ids:
            if message.device_action == SetDeviceState.TurnOff:
                switch.async_turn_off(self._hass, device_id)
            elif message.device_action == SetDeviceState.TurnOn:
                switch.async_turn_on(self._hass, device_id)
            else:
                pass


class HomeAssistentServer(object):
    def __init__(self, hass, config):
        # activate_timeout = config['voice_commands'].get('activate_timeout', 10)
        self._hass = hass
        self._server = None

    def handler_factory(self):
        return HomeAssistentHandler(self._hass)

    async def activate_handle(self, call):
        await self._server.send_protobuf_to_all(StartRecognition())

    async def run(self, domain):
        protocol = HASerrializeProtocol([SetDeviceState], logger)
        self._server = await create_server('0.0.0.0', 8083, self.handler_factory, protocol, logger)
        self._hass.services.async_register(domain, 'activate', self.activate_handle)


async def run(domain, hass, config) -> bool:
    server = HomeAssistentServer(hass, config)
    await server.run(domain)

    return True
