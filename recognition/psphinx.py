import os
from pocketsphinx.pocketsphinx import Decoder
from .base import HotwordRecognizer, HotwordRecognizerConfig


class Pocketsphinx(HotwordRecognizer):
    def __init__(self, config):
        super().__init__(config)
        self._decoder = Pocketsphinx._create_decoder(config)
        self._is_start = False

    @staticmethod
    def _create_decoder(config) -> Decoder:
        decoder_config = Decoder.default_config()
        decoder_config.set_string('-hmm', config.hmm)
        # decoder_config.set_string("-lm", config.lm)
        decoder_config.set_string('-dict', config.dict)
        decoder_config.set_string('-keyphrase', config.hotword)
        decoder_config.set_float('-kws_threshold', config.threshold)
        decoder_config.set_string('-logfn', os.devnull)

        return Decoder(decoder_config)

    def is_hotword(self, raw_frames) -> bool:
        if not self._is_start:
            self._is_start = True
            self._decoder.start_utt()

        self._decoder.process_raw(raw_frames, False, False)
        hypothesis = self._decoder.hyp()
        if hypothesis:
            if hypothesis.hypstr.find(self._config.hotword) >= 0:
                self._decoder.end_utt()
                self._is_start = False
                return True

        return False


class PocketsphinxConfig(HotwordRecognizerConfig):
    def __init__(self, hmm, dict, lm, hotword, threshold):
        self.hmm = hmm
        self.dict = dict
        self.lm = lm
        self.hotword = hotword
        self.threshold = threshold

    def create_phrase_recognizer(self):
        return Pocketsphinx(self)