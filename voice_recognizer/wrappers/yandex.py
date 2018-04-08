import http.client
import xml.etree.ElementTree
from voice_recognizer.stream_settings import StreamSettings
from voice_recognizer.wrappers.recognizer import RecognizerSettings, Recognizer


class Yandex(Recognizer):
    def __init__(self, settings):
        super().__init__(settings)
        self._recognize_host = settings.host
        self._recognize_url = settings.get_url()
        self._data_settings = None
        self._conn = None

    def recognize_start(self, data_settings: StreamSettings):
        self._data_settings = data_settings

        skips = {}
        self._conn = http.client.HTTPSConnection(self._recognize_host)
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
        root = xml.etree.ElementTree.fromstring(data.decode("utf-8"))
        if root.attrib['success'] == '0':
            return []

        return [child.text for child in root]


class YandexConfig(RecognizerSettings):
    def __init__(self, key, user_uuid, topic='queries', lang='ru-RU', disable_antimat=True):
        self.key = key
        self.user_uuid = user_uuid
        self.topic = topic
        self.lang = lang
        self.disable_antimat = disable_antimat
        self.host = 'asr.yandex.net'

    def create_recognizer(self):
        return Yandex(self)

    def get_url(self):
        tmp = '/asr_xml?uuid={}&key={}&topic={}&lang={}&disableAntimat={}'
        disable_antimat = str(self.disable_antimat).lower()
        return tmp.format(self.user_uuid, self.key, self.topic, self.lang, disable_antimat)
