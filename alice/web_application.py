import json
import logging
import random
from aiohttp import web
from nlp import Morphology
from etc import alice_entitis, alice_cloud_config


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

    async def process_heartbeat(self) -> Response:
        return Response("pong", end_session=True)

    async def process_request(self, command, is_new) -> Response:
        if is_new:
            text = ("Привет! Я помощник для управления частным умным домом. "
                    "Это приватный навык, поэтому для того, что бы я заработал, "
                    "произнесите кодовое слово. "
                    "Для помощи, скажите: Помощь. "
                    "Для выхода из навыка произнесите: Хватит.")
            return Response(text)

        cmd = self._morph.analyze(command)
        if 'stop' in cmd:
            texts = ["Пока", "Пока пока", "До свидания", "Увидимся", "Приходите ещё"]
            return Response(random.choice(texts), end_session=True)
        elif 'help' in cmd:
            text = ("Кошка Мурка - это приватный навык управления умным домом. "
                    "Я пока умею управлять только одним домом, поэтому мне нужно удостоверится, "
                    "что меня не запустил чужой человек. "
                    "Для этого скажите кодовое слово, без него я не смогу работать. "
                    "Для выхода из навыка произнесите: Хватит.")
            return Response(text)

        text1 = "Я не смогу вам помочь, пока вы не скажите правильное кодовое слово."
        text2 = ("Вы не угадали кодовое слово. "
                 "Для помощи, скажите: Помощь.")
        text3 = ("Попробуйте другое секретное слово. "
                 "Или для выхода из навыка скажите: Хватит.")
        text4 = ("Похоже вы не знаете пароля. "
                 "Извините, я вас не пущу играться чужим домом.")

        texts = [text1, text2, text3, text4]
        return Response(random.choice(texts))

    async def handler(self, request):
        data = await request.json()
        command = data["request"]["command"]
        is_new = data["session"]["new"]
        is_heartbeat = command == "ping"

        if not is_heartbeat:
            self._logger.info("in:{}".format(data))

        if is_heartbeat:
            response = await self.process_heartbeat()
        else:
            response = await self.process_request(command, is_new)

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

        if is_heartbeat:
            self._logger.debug("ping-pong")
        else:
            self._logger.info("out:{}".format(answer_str))
        return web.Response(text=answer_str)
