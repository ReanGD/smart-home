import collections
from voice_recognizer.device import Device
from voice_recognizer.streams import Stream
from voice_recognizer.stream_settings import StreamSettings
from voice_recognizer.wrappers.recognizer import RecognizerSettings
from voice_recognizer.wrap_snowboy import SnowboyWrap, SnowboyConfig
from voice_recognizer.wrap_pocketsphinx import PocketSphinxWrap, PocketSphinxConfig


class Recognizer(object):
    def __init__(self, recognizer_settings: RecognizerSettings, snowboy_config: SnowboyConfig,
                 pocket_sphinx_config: PocketSphinxConfig=None):
        self._stream = None
        self._recognizer = recognizer_settings.create_recognizer()
        self._snowboy = SnowboyWrap(snowboy_config)
        if pocket_sphinx_config is not None:
            self._hotword_detector = PocketSphinxWrap(pocket_sphinx_config)
        else:
            self._hotword_detector = self._snowboy

        # params
        timeout_before_phrase_ms = 3 * 1000
        timeout_after_phrase_ms = 2 * 1000
        timeout_speech_detect_ms = 500
        speech_detect_ratio = 0.9
        self._time_read_ms = 40

        # tmp values
        self._timeout_before_phrase_steps = int(timeout_before_phrase_ms / self._time_read_ms)
        self._timeout_after_phrase_steps = int(timeout_after_phrase_ms / self._time_read_ms)
        self._speech_detect_buffer_maxlen = int(timeout_speech_detect_ms / self._time_read_ms)
        self._speech_detect_threshold = speech_detect_ratio * self._speech_detect_buffer_maxlen

    def get_audio_settings(self,
                           device: Device,
                           device_index=None,
                           frames_per_buffer=2048) -> StreamSettings:
        return self._snowboy.get_audio_settings(device, device_index, frames_per_buffer)

    def _calc_frames_read(self, stream: Stream):
        frames_read = stream.get_settings().get_frames_count_by_duration_ms(self._time_read_ms)
        msg = 'Invalid value "frames_per_buffer" in stream.settings'
        assert frames_read <= stream.get_settings().frames_per_buffer, msg

        return frames_read

    def wait_hotword(self, stream: Stream):
        frames_read = self._calc_frames_read(stream)

        while True:
            frames = stream.read(frames_read)
            if len(frames) == 0:
                return False

            if self._hotword_detector.is_hotword(frames):
                return True

    def read_phrase(self, stream: Stream, timeout_sec=20) -> bool:
        timeout_steps = int(timeout_sec * 1000.0 / self._time_read_ms)
        assert timeout_steps > self._timeout_before_phrase_steps, 'Invalid arg "timeout_sec"'

        speech_detect_buffer = collections.deque(maxlen=self._speech_detect_buffer_maxlen)
        frames_read = self._calc_frames_read(stream)

        voice = []
        step = 0
        while speech_detect_buffer.count(True) <= self._speech_detect_threshold:
            frames = stream.read(frames_read)
            if len(frames) == 0:
                return False

            voice.append(frames)
            speech_detect_buffer.append(self._snowboy.is_speech(frames))
            step += 1

            # timeout before phrase
            if step >= self._timeout_before_phrase_steps:
                return False

        self._recognizer.recognize_start(stream.get_settings())
        voice = voice[-speech_detect_buffer.maxlen:]
        silent_step = 0
        state_speech = True
        for _ in range(step, timeout_steps):
            frames = stream.read(frames_read)
            if len(frames) == 0:
                return False

            voice.append(frames)
            speech_detect_buffer.append(self._snowboy.is_speech(frames))

            if not state_speech:
                if speech_detect_buffer.count(True) > self._speech_detect_threshold:
                    state_speech = True
            else:
                if speech_detect_buffer.count(False) > self._speech_detect_threshold:
                    self._recognizer.recognize_add_frames(voice)
                    voice.clear()
                    state_speech = False

            if state_speech:
                silent_step = 0
            else:
                silent_step += 1

            # timeout after phrase
            if silent_step >= self._timeout_after_phrase_steps:
                return True

        # total timeout
        if state_speech:
            self._recognizer.recognize_add_frames(voice)

        return True

    def recognize(self):
        return self._recognizer.recognize_finish()
