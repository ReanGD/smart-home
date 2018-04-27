import os
import audio
from recognition import Pocketsphinx, PocketsphinxConfig


def _get_pocket_sphinx() -> PocketsphinxConfig:
    base = '/home/rean/projects/git/smart-home/pocketsphinx/zero_ru_cont_8k_v3/'
    hmm = os.path.join(base, 'zero_ru.cd_semi_4000')
    # hmm = os.path.join(base, 'zero_ru.cd_cont_4000')
    # hmm = os.path.join(base, 'zero_ru.cd_semi_4000')
    dict = os.path.join(base, 'ru.dic')
    lm = os.path.join(base, 'ru.lm')
    hotword = 'абориген'
    threshold = 1e-40

    return PocketsphinxConfig(hmm, dict, lm, hotword, threshold)


class PocketSphinxWrap(Pocketsphinx):
    def __init__(self, config):
        super().__init__(config)


def run():
    pocket = PocketSphinxWrap(_get_pocket_sphinx())
    device = audio.Device()
    try:
        settings = audio.StreamSettings(device, device_index=None, sample_rate=16000)
        print("settings: {}".format(settings))
        mic = device.create_microphone_stream(settings)
        # mic = manager.create_data_stream(vr.AudioData.load_as_wav('/home/rean/projects/git/smart-home/record.wav', settings))

        ind = 0
        while True:
            frames = mic.read(settings.frames_per_buffer)
            if len(frames) == 0:
                break
            if pocket.is_hotword(frames):
                print('found {}'.format(ind))
                ind += 1
    except KeyboardInterrupt:
        pass
    finally:
        device.terminate()
