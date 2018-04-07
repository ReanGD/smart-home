import requests
import collections
from voice_recognizer.device import Device
from voice_recognizer.streams import Stream
from voice_recognizer.wrap_snowboy import SnowboyWrap
from voice_recognizer.wrap_pocketsphinx import PocketSphinxWrap, PocketSphinxConfig
from voice_recognizer.audio_data import AudioData
from voice_recognizer.stream_settings import StreamSettings


class Recognizer(object):
    def __init__(self, resource_filename, model_str, ya_key, ya_user,
                 pocket_sphinx_config: PocketSphinxConfig=None):
        self._stream = None
        self._ya_base_url = 'https://asr.yandex.net/asr_xml?uuid={}&key={}'.format(ya_user, ya_key)
        self._snowboy = SnowboyWrap(resource_filename, model_str, sensitivity=0.5, audio_gain=1.0)
        if pocket_sphinx_config is not None:
            self._hotword_detector = PocketSphinxWrap(pocket_sphinx_config)
        else:
            self._hotword_detector = self._snowboy

    def get_audio_settings(self,
                           device: Device,
                           device_index=None,
                           frames_per_buffer=2048) -> StreamSettings:
        return self._snowboy.get_audio_settings(device, device_index, frames_per_buffer)

    def wait_hotword(self, stream: Stream):
        settings = stream.get_settings()
        period_ms = 40
        frames_cnt = settings.get_frames_count_by_duration_ms(period_ms)
        assert frames_cnt <= settings.frames_per_buffer, "Invalid frames_per_buffer in settings"

        while True:
            frames = stream.read(frames_cnt)
            if len(frames) == 0:
                return False

            if self._hotword_detector.is_hotword(frames):
                return True

    def read_phrase(self, stream: Stream, timeout_sec=20):
        settings = stream.get_settings()
        period_ms = 20
        frames_cnt = settings.get_frames_count_by_duration_ms(period_ms)
        assert frames_cnt <= settings.frames_per_buffer, "Invalid frames_per_buffer in settings"

        voice = []
        silent_cnt = 0
        silent_max = int(2 * 1000.0 / period_ms)
        state_active = False
        ring_buffer = collections.deque(maxlen=30)
        for _ in range(0, int(timeout_sec * 1000.0 / period_ms)):
            frames = stream.read(frames_cnt)
            if len(frames) == 0:
                return None

            voice.append(frames)
            is_speech = self._snowboy.is_speech(frames)
            ring_buffer.append(is_speech)

            if not state_active:
                num_voiced = len([1 for speech in ring_buffer if speech])
                if num_voiced > 0.9 * len(ring_buffer):
                    state_active = True
            else:
                num_unvoiced = len([1 for speech in ring_buffer if not speech])
                if num_unvoiced > 0.9 * len(ring_buffer):
                    state_active = False

            if state_active:
                silent_cnt = 0
            else:
                silent_cnt += 1
                if silent_cnt > silent_max:
                    break

        return b''.join(voice[:-silent_max])

    def recognize_yandex(self, raw_date, settings):
        wav_data = AudioData(raw_date, settings).get_wav_data()

        url = self._ya_base_url + '&topic=queries&disableAntimat=true&lang=ru-RU'
        headers = {'Content-Type': 'audio/x-wav'}
        r = requests.post(url, headers=headers, data=wav_data)
        return r.text
