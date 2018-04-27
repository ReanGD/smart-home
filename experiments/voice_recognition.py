import soco
import audio
import config
from respeaker import pixel_ring
from recognition import Listener


def play():
    speakers = soco.discover()

    # Display a list of speakers
    for speaker in speakers:
        print("%s (%s)" % (speaker.player_name, speaker.ip_address))

    # Play a speaker
    speakers.pop().play()


def run():
    device = audio.Device()
    pixel_ring.off()
    try:
        recognizer_settings = config.yandex
        # recognizer_settings = vr.RawConfig()
        recognizer = Listener(config.pocket_sphinx, config.snowboy, recognizer_settings)
        settings = recognizer.get_stream_settings(device, device_index=None)
        print("settings: {}".format(settings))
        mic = device.create_microphone_stream(settings)

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
        device.terminate()