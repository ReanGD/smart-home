import audio
import config
from respeaker import pixel_ring
from recognition import Listener


def run(device_index=None):
    device = audio.Device()
    recognizer = None
    pixel_ring.off()
    try:
        recognizer_settings = config.yandex
        # hotword_settings = config.pocket_sphinx
        hotword_settings = config.http_activation

        recognizer = Listener(hotword_settings, config.snowboy, recognizer_settings)
        hotword_recognizer = recognizer.get_hotword_recognizer()
        phrase_recognizer = recognizer.get_phrase_recognizer()
        settings = recognizer.get_stream_settings(device, device_index=device_index)
        print("settings: {}".format(settings))
        mic = device.create_microphone_stream(settings)

        while True:
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

            audio.AudioData(phrase_recognizer.get_all_data(), settings).save_as_wav('record.wav')

            print(result)
            pixel_ring.off()
            hotword_recognizer.set_answer(result)
    except KeyboardInterrupt:
        pass
    finally:
        print('stop')
        pixel_ring.off()
        recognizer.close()
        device.terminate()