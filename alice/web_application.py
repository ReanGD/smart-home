import json
import logging
from aiohttp import web
from nlp import Morphology
from etc import alice_entitis


class Response:
    def __init__(self, text, end_session=False):
        self.text = text
        self.end_session = end_session


class WebApplication:
    def __init__(self):
        self._logger = logging.getLogger('alice')
        self._app = web.Application()
        self._morph = Morphology(alice_entitis)

    def run(self, socket):
        self._app.add_routes([web.get('/', self.index),
                              web.post('/', self.handler)])
        web.run_app(self._app, path=socket)

    async def index(self, request):
        return web.Response(text="Hello 3")

    async def process_request(self, command, is_new) -> Response:
        if is_new:
            text = ("Привет, я помощник для управления частным умным домом. "
                    "Это приватный навык, для авторизации скажите кодовое слово. "
                    "Если вы его не знаете, то для выхода скажите хватит.")
            return Response(text)

        cmd = self._morph.analyze(command)
        if 'stop' in cmd:
            text = "Пока"
            return Response(text, end_session=True)
        elif 'help' in cmd:
            text = ("Я могу управлять умным домом. "
                    "Для того, что бы начать, скажите кодовое слово. "
                    "Если вы его не знаете, то для выхода скажите хватит.")
            return Response(text)

        text = "Неверный код доступа"
        return Response(text)

    async def handler(self, request):
        data = await request.json()
        self._logger.info("in:{}".format(data))
        response = await self.process_request(data["request"]["command"], data["session"]["new"])

        answer = {
            "response": {
                "text": response.text,
                "end_session": response.end_session,
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
        return web.Response(text=answer_str)
