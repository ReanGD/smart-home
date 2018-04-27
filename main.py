# import vad_webrtcvad
# import vad_snowboy
# import vad_test
# import pocketsphinx_test
import config
import wrap_speech_recognition
import audio
from skills import Skills
import experiments.voice_recognition
import experiments.hotword


def run_speech_recognition():
    wrap_speech_recognition.run()


def print_list():
    manager = audio.Device()
    try:
        for ind in range(manager.get_device_count()):
            print(manager.get_device_info_by_index(ind))
            print()
    finally:
        manager.terminate()


def test_record():
    seconds = 15

    manager = audio.Device()
    try:
        settings = audio.StreamSettings(manager, device_index=None)
        print("settings: {}".format(settings))
        mic = manager.create_microphone_stream(settings)

        step_cnt = int(settings.sample_rate / settings.frames_per_buffer * seconds)
        print("start record...")
        data = b''.join([mic.read(settings.frames_per_buffer) for _ in range(step_cnt)])
        print("stop record...")

        audio.AudioData(data, settings).save_as_wav("record.wav")
    finally:
        manager.terminate()


def test_vad():
    device = audio.Device()
    try:
        vad_webrtcvad.run(device)
        vad_test.run(device)
        vad_snowboy.run(device)
    finally:
        device.terminate()


def skills():
    obj = Skills(config.skills)
    print(obj.run('Наутилус'))


def main():
    print("start")
    # run_speech_recognition()
    # print_list()
    # test_record()
    # test_vad()
    # skills()

    # experiments.voice_recognition.run()
    experiments.hotword.run()
    print("stop")


if __name__ == '__main__':
    main()
