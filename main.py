import asyncio
from experiments import *


async def run():
    print("start")

    # device_info.run()
    await record.run(8)
    # voice_recognition.run(8)
    # yaproto.run(8)

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
