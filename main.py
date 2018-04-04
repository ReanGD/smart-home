import vad_webrtcvad
import vad_snowboy
import vad_test
import settings
import wrap_speech_recognition
import voice_recognizer as vr


def run_speech_recognition():
    wrap_speech_recognition.run()


def test_record():
    seconds = 15

    manager = vr.Device()
    try:
        settings = vr.StreamSettings(manager)
        print("settings: {}".format(settings))
        mic = manager.create_microphone_stream(settings)

        step_cnt = int(settings.sample_rate / settings.frames_per_buffer * seconds)
        print("start record...")
        data = b''.join([mic.read(settings.frames_per_buffer) for _ in range(step_cnt)])
        print("stop record...")

        vr.AudioData(data, settings).save_as_wav("record.wav")
    finally:
        manager.terminate()


def test_vad():
    device = vr.Device()
    try:
        vad_webrtcvad.run(device)
        # vad_test.run(device)
        vad_snowboy.run(device)
    finally:
        device.terminate()


def test_voice_recognition():
    manager = vr.Device()
    try:
        recognizer = vr.Recognizer(settings.snowboy_res, settings.snowboy_model,
                                   settings.ya_key, settings.ya_user)
        set = recognizer.get_audio_settings(manager)
        print("settings: {}".format(set))
        mic = manager.create_microphone_stream(set)

        print("start wait hotword...")
        if not recognizer.wait_hotword(mic):
            print("error")
            return

        print("start record...")
        data = recognizer.read_phrase(mic)
        if data is None:
            print("error")
            return

        print("start send...")
        # vr.AudioData(data, set).save_as_wav("record.wav")
        result = recognizer.recognize_yandex(data, set)
        print(result)
    finally:
        manager.terminate()


def main():
    print("start")
    # run_speech_recognition()
    # test_record()
    # test_vad()
    test_voice_recognition()
    print("stop")


if __name__ == '__main__':
    main()
