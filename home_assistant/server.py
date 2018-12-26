import json
from aiohttp import web
from logging import getLogger
from homeassistant.core import HomeAssistant
from homeassistant.components.http import HomeAssistantView
from .commands import HassCommands


class AliceHandlerView(HomeAssistantView):
    """Handle Alice."""

    url = '/api/alice/handler'
    name = 'api:alice:handler'

    def __init__(self, domain: str, default_place: str):
        self._logger = getLogger(domain)
        self._command = HassCommands(self._logger, default_place)

    async def post(self, request):
        hass = request.app['hass']
        data = await request.json()
        self._logger.info("in:{}".format(data))
        is_new = data["session"]["new"]
        command = data["request"]["command"]

        end_session = False
        if is_new:
            text = 'Привет'
        elif await self._command.execute(hass, command):
            text = 'Выполняю'
        else:
            text = 'Я не могу это сделать'

        answer = {
            "response": {
                "text": text,
                "end_session": end_session,
            },
            "session": {
                "session_id": data["session"]["session_id"],
                "message_id": data["session"]["message_id"],
                "user_id": data["session"]["user_id"],
            },
            "version": data["version"]
        }
        answer_str = json.dumps(answer, ensure_ascii=False)

        self._logger.info("out:{}".format(answer_str))
        return web.Response(text=answer_str, content_type='application/json')


async def run(domain: str, hass: HomeAssistant, config) -> bool:
    default_place = config['smart_home'].get('default_place', 'livingroom')
    hass.http.register_view(AliceHandlerView(domain, default_place))

    return True
