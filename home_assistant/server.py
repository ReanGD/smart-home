from logging import Logger, getLogger
from homeassistant.core import HomeAssistant
from etc import HassTransportConfig
from protocols.transport import TCPServerConnection, TCPServer
from protocols.home_assistant import (HASerrializeProtocol, StartRecognition,
                                      UserTextCommand, UserTextCommandResult)
from .commands import HassCommands


class HomeAssistentConnection(TCPServerConnection):
    def __init__(self, logger: Logger, hass: HomeAssistant):
        super().__init__(logger)
        self._commands = HassCommands(logger, hass, 'livingroom')

    async def on_user_text_command(self, message: UserTextCommand):
        is_finished = self._commands.execute(message.text)
        await self.send(UserTextCommandResult(isFinished=is_finished))


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
