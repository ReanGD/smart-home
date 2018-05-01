from os import devnull
from pocketsphinx.pocketsphinx import Decoder
from .base import HotwordRecognizer, HotwordRecognizerConfig
from .audio_settings import AudioSettings


class Pocketsphinx(HotwordRecognizer):
    def __init__(self, config):
        super().__init__(config)
        self._decoder = Pocketsphinx._create_decoder(config)
        self._audio_settings = AudioSettings(channels=1, sample_rate=config.sample_rate)
        self._is_start = False

    def get_audio_settings(self) -> AudioSettings:
        return self._audio_settings

    def get_frate(self) -> int:
        return int(self._decoder.get_config().get_int('-frate'))

    @staticmethod
    def _create_decoder(config) -> Decoder:
        decoder_config = Decoder.default_config()
        decoder_config.set_string('-hmm', config.hmm)
        if config.lm is not None:
            decoder_config.set_string("-lm", config.lm)
        else:
            decoder_config.set_string('-keyphrase', config.hotword)
            decoder_config.set_float('-kws_threshold', config.threshold)
        decoder_config.set_string('-dict', config.dict)
        decoder_config.set_boolean('-remove_noise', config.remove_noise)
        decoder_config.set_float('-samprate', config.sample_rate)
        decoder_config.set_string('-logfn', devnull)

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
    def __init__(self, hmm, dict, lm, hotword, threshold, sample_rate, remove_noise):
        self.hmm = hmm
        self.dict = dict
        self.lm = lm
        self.hotword = hotword
        self.threshold = threshold
        self.sample_rate = sample_rate
        self.remove_noise = remove_noise

    def create_hotword_recognizer(self):
        return Pocketsphinx(self)
