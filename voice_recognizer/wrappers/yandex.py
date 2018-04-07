import requests
from voice_recognizer.wrappers.recognizer import RecognizerSettings, Recognizer
from voice_recognizer.audio_data import AudioData


class Yandex(Recognizer):
    def __init__(self, settings):
        super().__init__(settings)
        self._recognize_url = settings.get_url()

    def recognize(self, audio_date: AudioData):
        headers = {'Content-Type': 'audio/x-wav'}
        r = requests.post(self._recognize_url, headers=headers, data=audio_date.get_wav_data())

        return r.text


class YandexConfig(RecognizerSettings):
    def __init__(self, key, user_uuid, topic='queries', lang='ru-RU', disable_antimat=True):
        self.key = key
        self.user_uuid = user_uuid
        self.topic = topic
        self.lang = lang
        self.disable_antimat = disable_antimat

    def create_recognizer(self):
        return Yandex(self)

    def get_url(self):
        tmp = 'https://asr.yandex.net/asr_xml?uuid={}&key={}&topic={}&lang={}&disableAntimat={}'
        disable_antimat = str(self.disable_antimat).lower()
        return tmp.format(self.user_uuid, self.key, self.topic, self.lang, disable_antimat)
