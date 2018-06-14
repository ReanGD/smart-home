import audio
import config


def run(index=None):
    device = audio.Device()
    settings = audio.StreamSettings(device, device_index=index)
    recognizer = config.yandex_protobuf.create_phrase_recognizer()
    try:
        print("settings: {}".format(settings))
        mic = device.create_microphone_stream(settings)
        recognizer.recognize_start(settings)
        print("start record...")

        while True:
            recognizer.recognize_add_frames([mic.read(settings.frames_per_buffer)])

    except KeyboardInterrupt:
        print("stop record...")
    finally:
        recognizer.recognize_finish()
        recognizer.close()
        device.terminate()
