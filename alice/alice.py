import json
from aiohttp import web
from argparse import ArgumentParser


async def index(request):
    return web.Response(text="Hello 2")


async def process_request(command, is_new):
    if is_new:
        text = ("Привет, я помощник для управления частным умным домом."
                "Для работы навыка скажите кодовое слово."
                "Если вы его не знаете, то для выхода скажите слово хватит.")
    else:
        text = "Неверный код доступа"
    return text


async def handler(request):
    data = await request.json()
    print("in:\n{}".format(data))
    text = await process_request(data["request"]["command"], data["session"]["new"])

    answer = {
        "response": {
            "text": text,
            "end_session": False
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


def run(socket):
    app = web.Application()
    app.add_routes([web.get('/', index),
                    web.post('/', handler)])
    web.run_app(app, path=socket)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("--socket")
    args = parser.parse_args()
    run(args.socket)
