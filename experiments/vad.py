# import vad_webrtcvad
# import vad_snowboy
# import vad_test
import audio


def run():
    device = audio.Device()
    try:
        vad_webrtcvad.run(device)
        vad_test.run(device)
        vad_snowboy.run(device)
    finally:
        device.terminate()