import asyncio
import logging
from sys import stdout
from experiments import *


def init_logger():
    handler = logging.StreamHandler(stdout)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
    handler.setFormatter(formatter)

    logger = logging.getLogger('yandex_api')
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    logger = logging.getLogger('demo')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)


async def run():
    print("start")

    device_index = 0
    # await device_info.run()
    # await record.run(device_index)
    # await demo.run(device_index)
    await yandex_recognition.run(device_index)

    # voice_recognition.run(device_index)
    # vad.run()
    # wrap_speech_recognition.run()
    # skills.run()
    # hotword.run()
    # hotword_mic.run()
    # split_file.run()
    # pocketsphinx_recognition.run()
    # ps_test.run()

    print("stop")


def main():
    init_logger()
    loop = asyncio.get_event_loop()
    task = None
    try:
        task = run()
        loop.run_until_complete(task)
    except KeyboardInterrupt:
        task.close()
    finally:
        loop.close()


if __name__ == '__main__':
    main()
