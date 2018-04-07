import os
from pocketsphinx.pocketsphinx import Decoder


class PocketSphinxConfig(object):
    def __init__(self, hmm, dict, lm, hotword):
        self.hmm = hmm
        self.dict = dict
        self.lm = lm
        self.hotword = hotword


class PocketSphinxWrap(object):
    def __init__(self, config: PocketSphinxConfig):
        self._config = config
        self._decoder = self._create_decoder()
        self._is_start = False

    def _create_decoder(self) -> Decoder:
        config = Decoder.default_config()
        config.set_string('-hmm', self._config.hmm)
        config.set_string("-lm", self._config.lm)
        config.set_string('-dict', self._config.dict)
        config.set_string('-logfn', os.devnull)

        return Decoder(config)

    def get_config(self):
        return self._config

    def is_hotword(self, frames):
        if not self._is_start:
            self._is_start = True
            self._decoder.start_utt()

        self._decoder.process_raw(frames, False, False)
        hypothesis = self._decoder.hyp()
        if hypothesis:
            if hypothesis.hypstr.find(self._config.hotword) >= 0:
                self._decoder.end_utt()
                self._is_start = False
                return True

        return False
