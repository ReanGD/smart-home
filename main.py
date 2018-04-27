import vad_webrtcvad
import vad_snowboy
import vad_test
import config
import wrap_speech_recognition
import audio as vr
import pocketsphinx_test
from skills import Skills
from respeaker.pixel_ring import pixel_ring


def run_speech_recognition():
    wrap_speech_recognition.run()


def print_list():
    manager = vr.Device()
    try:
        for ind in range(manager.get_device_count()):
            print(manager.get_device_info_by_index(ind))
            print()
    finally:
        manager.terminate()


def test_record():
    seconds = 15

    manager = vr.Device()
    try:
        settings = vr.StreamSettings(manager, device_index=None)
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
        vad_test.run(device)
        vad_snowboy.run(device)
    finally:
        device.terminate()


def play():
    import soco
    speakers = soco.discover()

    # Display a list of speakers
    for speaker in speakers:
        print("%s (%s)" % (speaker.player_name, speaker.ip_address))

    # Play a speaker
    speakers.pop().play()


def test_voice_recognition():
    manager = vr.Device()
    pixel_ring.off()
    try:
        recognizer_settings = config.yandex
        # recognizer_settings = vr.RawConfig()
        recognizer = vr.Recognizer(recognizer_settings, config.snowboy, config.pocket_sphinx)
        settings = recognizer.get_audio_settings(manager, device_index=None)
        print("settings: {}".format(settings))
        mic = manager.create_microphone_stream(settings)

        print("start wait hotword...")
        if not recognizer.wait_hotword(mic):
            print("error")
            return

        pixel_ring.set_volume(12)
        print("start record...")
        if not recognizer.read_phrase(mic):
            print("error read phrase")
            return

        print("start send...")
        pixel_ring.wait()
        result = recognizer.recognize()

        # result.save_as_wav("record.wav")
        if result is not None and 'включи музыку' in result:
            play()
        print(result)
    except KeyboardInterrupt:
        pass
    finally:
        pixel_ring.off()
        manager.terminate()


def skills():
    obj = Skills(config.skills)
    print(obj.run('Наутилус'))


def main():
    print("start")
    # run_speech_recognition()
    # print_list()
    # test_record()
    # test_vad()
    # test_voice_recognition()
    # play()
    # skills()
    pocketsphinx_test.run()
    print("stop")


if __name__ == '__main__':
    main()
