import json
from aiohttp import web
from argparse import ArgumentParser
from nlp import Morphology
from etc import alice_entitis


class Response:
    def __init__(self, text, end_session=False):
        self.text = text
        self.end_session = end_session


class WebApplication:
    def __init__(self):
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
            text = ("Привет, я помощник для управления частным умным домом."
                    "Это приватный навык, для авторизации скажите кодовое слово."
                    "Если вы его не знаете, то для выхода скажите хватит.")
            return Response(text)

        cmd = self._morph.analyze(command)
        if 'stop' in cmd:
            text = "Пока"
            return Response(text, end_session=True)

        text = "Неверный код доступа"
        return Response(text)

    async def handler(self, request):
        data = await request.json()
        print("in:\n{}".format(data))
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
        answer_str = json.dumps(answer)

        print("out:\n{}".format(answer_str))
        return web.Response(text=answer_str)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("--socket")
    args = parser.parse_args()
    WebApplication().run(args.socket)
