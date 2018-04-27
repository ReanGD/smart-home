import os
from audio import PocketSphinxConfig
from pocketsphinx.pocketsphinx import Decoder
import audio as vr


def _get_pocket_sphinx() -> PocketSphinxConfig:
    base = '/home/rean/projects/git/smart-home/pocketsphinx/zero_ru_cont_8k_v3/'
    # hmm = os.path.join(base, 'zero_ru.cd_cont_4000')
    # hmm = os.path.join(base, 'zero_ru.cd_semi_4000')
    hmm = os.path.join(base, 'zero_ru.cd_ptm_4000')
    # cont lm: 9,  -20: 1   -30: 5   -40: 7   -50: 8
    # semi lm: 10, -20: 10  -30: 10  -40: 10  -50: 10
    # ptm  lm: 10, -20: 7   -30: 9   -40: 10  -50: 10
    dict = os.path.join(base, 'ru.dic')
    lm = os.path.join(base, 'ru.lm')
    hotword = 'абориген'
    threshold = 1e-40

    return PocketSphinxConfig(hmm, dict, lm, hotword, threshold)


class PocketSphinxWrap(object):
    def __init__(self):
        self._config = _get_pocket_sphinx()
        self._decoder = self._create_decoder()
        self._is_start = False
        self.in_speech_bf = False

    def _create_decoder(self) -> Decoder:
        config = Decoder.default_config()
        config.set_string('-hmm', self._config.hmm)
        # config.set_string('-lm', self._config.lm)
        config.set_string('-dict', self._config.dict)
        config.set_string('-logfn', os.devnull)

        config.set_string('-keyphrase', 'абориген')
        config.set_float('-kws_threshold', 1e-40)

        print('samprate = {}'.format(config.get_float('-samprate')))

        decoder = Decoder(config)

        # decoder.set_kws("keywords", '/home/rean/projects/git/smart-home/pocketsphinx/zero_ru_cont_8k_v3/keywords.txt')
        # decoder.set_search("keywords")

        return decoder

    def is_hotword(self, frames):
        if not self._is_start:
            self._is_start = True
            self._decoder.start_utt()
            print('start utt')

        self._decoder.process_raw(frames, False, False)
        hypothesis = self._decoder.hyp()
        if hypothesis:
            if hypothesis.hypstr.find(self._config.hotword) >= 0:
                self._decoder.end_utt()
                self._is_start = False
                return True

        return False


def run():
    pocket = PocketSphinxWrap()
    manager = vr.Device()
    try:
        settings = vr.StreamSettings(manager, device_index=None, sample_rate=16000)
        print("settings: {}".format(settings))
        mic = manager.create_microphone_stream(settings)
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
        manager.terminate()
