import vad_webrtcvad
import vad_snowboy
import vad_test
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

        vr.AudioData(data, settings).write_wav_data("record.wav")
    finally:
        manager.terminate()


def test_vad():
    device = vr.Device()
    try:
        # vad_webrtcvad.run(device)
        vad_test.run(device)
        # vad_snowboy.run(device)
    finally:
        device.terminate()

def main():
     print("start")
     # run_speech_recognition()
     # test_record()
     test_vad()
     print("stop")


if __name__ == '__main__':
    main()
