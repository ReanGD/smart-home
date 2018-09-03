import sys


sm = '/home/rean/projects/git/smart-home'
if sm not in sys.path:
    sys.path.append(sm)


from home_assistant.server import run


DOMAIN = 'voice_commands'


async def async_setup(hass, config):
    return await run(DOMAIN, hass, config)
