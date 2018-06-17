import asyncio
import logging
from sys import stdout
from experiments import *


def init_logger():
    handler = logging.StreamHandler(stdout)

    logger = logging.getLogger('yanader_transport')
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)


async def run():
    print("start")

    # device_info.run()
    # await record.run(8)
    await yaproto.run(8)
    # voice_recognition.run(8)

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
