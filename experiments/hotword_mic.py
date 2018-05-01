import os
from os import devnull
import audio
from prettytable import PrettyTable
from pocketsphinx.pocketsphinx import Decoder
from recognition import (Pocketsphinx, Snowboy, PocketsphinxConfig, SnowboyConfig,
                         get_common_settings)


def root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _get_pocket_sphinx() -> PocketsphinxConfig:
    base = os.path.join(root(), 'pocketsphinx', 'zero_ru_cont_8k_v3')

    hmm = os.path.join(base, 'zero_ru.cd_semi_4000')  # - mobile?
    # hmm = os.path.join(base, 'zero_ru.cd_cont_4000')
    # hmm = os.path.join(base, 'zero_ru.cd_ptm_4000') - mobile?

    dict = os.path.join(base, 'ru.dic')
    # lm = os.path.join(base, 'ru.lm')
    lm = None
    # hotwords = ['алекса', 'алекс']
    hotwords = ['василий']
    threshold = 1e-20
    sample_rate = 16000
    remove_noise = True
    # all noise marked as SIL => remove_noise = False

    return PocketsphinxConfig(hmm, dict, lm, hotwords, threshold, sample_rate, remove_noise)


def run():
    pocket = Pocketsphinx(_get_pocket_sphinx())
    device = audio.Device()
    try:
        settings = audio.StreamSettings(device, device_index=None, sample_rate=16000)
        print("settings: {}".format(settings))
        mic = device.create_microphone_stream(settings)

        ind_pocket = 0
        while True:
            frames = mic.read(settings.frames_per_buffer)
            if len(frames) == 0:
                break

            if pocket.is_hotword(frames):
                ind_pocket += 1
                print('found pocket {}'.format(ind_pocket))

    except KeyboardInterrupt:
        pass
    finally:
        device.terminate()
