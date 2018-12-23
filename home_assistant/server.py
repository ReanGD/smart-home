import json
from aiohttp import web
from logging import getLogger
from homeassistant.core import HomeAssistant
from .commands import HassCommands


class HomeAssistentServer(object):
    def __init__(self, domain: str, hass: HomeAssistant, default_place: str):
        self._hass = hass
        self._domain = domain
        self._app = web.Application()
        self._logger = getLogger(domain)
        self._commands = HassCommands(self._logger, hass, default_place)

    # async def activate_handle(self, call):
    #     await self._server.send_to_all(StartRecognition())

    async def _index(self, _request):
        return web.Response(text="Hello 3")

    async def _handler(self, request):
        data = await request.json()
        self._logger.info("in:{}".format(data))
        is_new = data["session"]["new"]
        command = data["request"]["command"]

        end_session = False
        if is_new:
            text = 'Привет'
        elif await self._commands.execute(command):
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

    async def run(self, port: int):
        self._app.add_routes([web.get('/', self._index),
                              web.post('/', self._handler)])
        await self.run_app(self._app, port=port, loop=self._hass.loop)
        # self._hass.services.async_register(self._domain, 'activate', self.activate_handle)

    async def run_app(self, app, port, loop, print=print):
        import asyncio
        from aiohttp.web_runner import AppRunner, GracefulExit, TCPSite
        from aiohttp import helpers
        from aiohttp.log import access_logger

        if asyncio.iscoroutine(app):
            app = await app

        runner = AppRunner(app, handle_signals=True,
                           access_log_class=helpers.AccessLogger,
                           access_log_format=helpers.AccessLogger.LOG_FORMAT,
                           access_log=access_logger)

        await runner.setup()

        try:
            site = TCPSite(runner, port=port, shutdown_timeout=60.0, ssl_context=None, backlog=128,
                           reuse_address=None, reuse_port=None)
            await site.start()
            # try:
            #     if print:  # pragma: no branch
            #         names = sorted(str(s.name) for s in runner.sites)
            #         print("======== Running on {} ========\n"
            #               "(Press CTRL+C to quit)".format(', '.join(names)))
            #     loop.run_forever()
            # except (GracefulExit, KeyboardInterrupt):  # pragma: no cover
            #     pass
        finally:
            pass
            # await runner.cleanup()

        # if hasattr(loop, 'shutdown_asyncgens'):
        #     loop.run_until_complete(loop.shutdown_asyncgens())
        # loop.close()


async def run(domain: str, hass: HomeAssistant, config) -> bool:
    port = int(config['smart_home'].get('port', 8383))
    default_place = config['smart_home'].get('default_place', 'livingroom')
    server = HomeAssistentServer(domain, hass, default_place)
    await server.run(port)

    return True
