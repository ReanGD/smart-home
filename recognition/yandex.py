from http.client import HTTPSConnection
from xml.etree.ElementTree import fromstring
from audio import StreamSettings
from .base import PhraseRecognizer, PhraseRecognizerConfig


class Yandex(PhraseRecognizer):
    def __init__(self, config):
        super().__init__(config)
        self._recognize_host = config.host
        self._recognize_url = config.get_url()
        self._data_settings = None
        self._conn = None

    def recognize_start(self, data_settings: StreamSettings):
        self._data_settings = data_settings

        skips = {}
        self._conn = HTTPSConnection(self._recognize_host)
        self._conn.putrequest('POST', self._recognize_url, **skips)
        self._conn.putheader('Transfer-Encoding', 'chunked')
        self._conn.putheader('Content-Type', 'audio/x-pcm;bit=16;rate=16000')
        self._conn.endheaders()

    def recognize_add_frames(self, raw_frames):
        data = b''.join(raw_frames)
        self._conn.send(hex(len(data))[2:].encode() + b'\r\n' + data + b'\r\n')

    def recognize_finish(self):
        self._conn.send(b'0\r\n\r\n')
        res = self._conn.getresponse()

        if res.status != 200:
            # print(res.status, res.reason)
            return None

        data = res.read()
        root = fromstring(data.decode("utf-8"))
        if root.attrib['success'] == '0':
            return []

        return [child.text for child in root]


class YandexConfig(PhraseRecognizerConfig):
    def __init__(self, key, user_uuid, topic='queries', lang='ru-RU', disable_antimat=True):
        self.key = key
        self.user_uuid = user_uuid
        self.topic = topic
        self.lang = lang
        self.disable_antimat = disable_antimat
        self.host = 'asr.yandex.net'

    def create_phrase_recognizer(self):
        return Yandex(self)

    def get_url(self):
        tmp = '/asr_xml?uuid={}&key={}&topic={}&lang={}&disableAntimat={}'
        disable_antimat = str(self.disable_antimat).lower()
        return tmp.format(self.user_uuid, self.key, self.topic, self.lang, disable_antimat)
