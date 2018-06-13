import logging
from sys import stdout
from time import sleep
from select import select
from ssl import wrap_socket
from socket import socket, AF_INET, SOCK_STREAM
from concurrent.futures import ThreadPoolExecutor
from pyaudio import paInt16
from audio import StreamSettings
from .base import PhraseRecognizer, PhraseRecognizerConfig
from .audio_settings import AudioSettings
from .yandex_proto.basic_pb2 import ConnectionResponse
from .yandex_proto.voiceproxy_pb2 import ConnectionRequest, AddData, AddDataResponse, AdvancedASROptions


logger = logging.getLogger('yandex_protobuf')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stdout)
logger.addHandler(handler)


class YandexProtobufError(RuntimeError):
    def __init__(self, message):
        RuntimeError.__init__(self, message)


class Transport(object):
    def __init__(self, host, port):
        logger.debug('Start connecting to %s:%s', host, port)
        tries = 5
        while tries > 0:
            try:
                s = wrap_socket(socket(AF_INET, SOCK_STREAM))
                s.connect((host, port))
                self._socket = s
                logger.info('Connected to %s:%s', host, port)
                break
            except Exception as ex:
                logger.info('Error connecting to %s:%s, message: %s', host, port, ex)
                tries -= 1
                if tries == 0:
                    raise ex
                else:
                    sleep(1)

    def send(self, data):
        while True:
            try:
                rlist, wlist, xlist = select([], [self._socket], [self._socket], 0.1)
                if len(xlist):
                    raise YandexProtobufError("Send unavailable")
                if len(wlist) != 0:
                    self._socket.send(data.encode("utf-8") if type(data) == str else data)
                    break
            except Exception as e:
                raise e

    def recv(self, length, decode=True):
        res = b""
        while True:
            try:
                res += self._socket.recv(length - len(res))
                if len(res) < length:
                    rlist, _, xlist = select([self._socket], [], [self._socket], 0.1)
                else:
                    if decode:
                        return res.decode("utf-8")
                    else:
                        return res
            except Exception as e:
                raise e

    def send_protobuf(self, protobuf):
        message = protobuf.SerializeToString()
        self._socket.send(hex(len(message))[2:].encode("utf-8"))
        self._socket.send(b'\r\n')
        begin = 0
        while begin < len(message):
            begin += self._socket.send(message[begin:])

    def recv_message(self):
        size = b''
        while True:
            symbol = self._socket.recv(1)

            if len(symbol) == 0:
                raise YandexProtobufError('Backend closed connection')

            assert(len(symbol) == 1), 'Bad symbol len from socket ' + str(len(symbol))

            if symbol == b'\r':
                self._socket.recv(1)
                break
            else:
                size += symbol

        size_int = int(b'0x' + size, 0)
        if size_int > 0:
            result = b''
            while len(result) < size_int:
                result += self._socket.recv(size_int - len(result), False)
            assert (len(result) == size_int), 'Invalid message size'
            return result
        return ''

    def recv_protobuf(self, *protobuf_types):
        saved_exception = None

        message = self.recv_message()
        for proto_type in protobuf_types:
            response = proto_type()
            try:
                response.ParseFromString(message)
                return response
            except Exception as exc:
                saved_exception = exc

        raise saved_exception

    def recv_protobuf_if_any(self, *protobuf_types):
        rlist, wlist, xlist = select([self._socket], [], [self._socket], 0)
        if len(rlist) != 0:
            return self.recv_protobuf(*protobuf_types)
        else:
            return None

    def close(self):
        self._socket.close()


class Connection(Transport):
    def __init__(self, config):
        super().__init__(config.host, config.port)
        self._config = config
        self._session_id = "not-set"

    def connect(self):
        self._upgrade_connection()
        response = self._send_connection_request()
        if response.responseCode != 200:
            raise Connection._error_from_response(response, 'Wrong response from server')

        self._session_id = response.sessionId

    def add_data(self, chunk):
        if chunk is None:
            self.send_protobuf(AddData(lastChunk=True))
        else:
            self.send_protobuf(AddData(lastChunk=False, audioData=chunk))

    def get_response_if_ready(self):
        response = self.recv_protobuf_if_any(AddDataResponse, ConnectionResponse)

        if isinstance(response, ConnectionResponse):
            raise Connection._error_from_response(response, 'Bad AddData response')

        if response is not None:
            if response.responseCode != 200:
                raise Connection._error_from_response(response, 'Wrong response from server')

        return response

    @staticmethod
    def _error_from_response(response, text):
        error_text = '{}, status_code={}'.format(text, response.responseCode)
        if response.HasField("message"):
            error_text += ', message is "{}"'.format(response.message)
        return YandexProtobufError(error_text)

    def _upgrade_connection(self):
        request = ('GET /asr_partial_checked HTTP/1.1\r\n'
                   'User-Agent: {app}\r\n'
                   'Host: {host}:{port}\r\n'
                   'Upgrade: dictation\r\n\r\n').format(app=self._config.app,
                                                        host=self._config.host,
                                                        port=self._config.port)
        logger.debug('Start upgrade connection')
        self.send(request)
        check = 'HTTP/1.1 101 Switching Protocols'
        buffer = ''

        while not buffer.startswith(check) or not buffer.endswith('\r\n\r\n'):
            buffer += self.recv(1)
            if len(buffer) > 300:
                raise YandexProtobufError('Unable to upgrade connection')

    def _send_connection_request(self):
        advanced_asr_options = AdvancedASROptions(
            partial_results=True,
            # beam=-1,
            # lattice_beam=-1,
            # lattice_nbest=-1,
            utterance_silence=120,
            # allow_multi_utt=True,
            # chunk_process_limit=100,
            # cmn_window=600,
            # cmn_latency=150,
            capitalize=False,
            expected_num_count=0,
            # grammar=,
            # srgs=,
            biometry='gender,age,group,children,emotion',
            use_snr=False,
            # snr_flags=,
            # biometry_group=,
            manual_punctuation=False
        )

        request = ConnectionRequest(
            speechkitVersion='',
            serviceName='asr_dictation',
            uuid=self._config.user_uuid,
            apiKey=self._config.api_key,
            applicationName=self._config.app,
            device='desktop',
            coords='0, 0',
            topic=self._config.topic,
            lang=self._config.lang,
            format='audio/x-pcm;bit=16;rate=16000',
            punctuation=True,
            disableAntimatNormalizer=self._config.disable_antimat,
            advancedASROptions=advanced_asr_options
        )

        logger.debug('Start send connection request')
        self.send_protobuf(request)
        return self.recv_protobuf(ConnectionResponse)


class YandexProtobuf(PhraseRecognizer):
    def __init__(self, config):
        super().__init__(config)
        self._data_settings = None
        self._conn = None
        self._audio_settings = AudioSettings(channels=1, sample_format=paInt16, sample_rate=16000)
        self._connection = None
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._executor.submit(self._check_result)

    def get_audio_settings(self) -> AudioSettings:
        return self._audio_settings

    def _check_result(self):
        while True:
            try:
                if self._connection is not None:
                    response = self._connection.get_response_if_ready()
                    if response is not None:
                        if len(response.recognition) != 0:
                            for bio in response.bioResult:
                                print('{} {} {}'.format(bio.classname, bio.confidence, bio.tag))
                        for ind, phrase in enumerate(response.recognition):
                            words = ['{}({})'.format(word.value, word.confidence) for word in phrase.words]
                            print('{}: {}'.format(ind, ' '.join(words)))
                    sleep(0.01)
                else:
                    sleep(0.2)
            except Exception as e:
                print(e)
                return

    def _recognize_start(self, data_settings: StreamSettings):
        self._data_settings = data_settings
        self._connection = Connection(self.get_config())
        self._connection.connect()

    def _add_data(self, data):
        self._connection.add_data(data)

    def recognize_finish(self):
        self._connection.close()
        self._connection = None

    def close(self):
        self._executor.shutdown(False)


class YandexProtobufConfig(PhraseRecognizerConfig):
    def __init__(self, api_key, user_uuid, topic='queries', lang='ru-RU', disable_antimat=True):
        self.api_key = api_key
        self.user_uuid = user_uuid
        self.topic = topic
        self.lang = lang
        self.disable_antimat = disable_antimat
        self.host = 'asr.yandex.net'
        self.port = 443
        self.app = 'SmartHome'

    def create_phrase_recognizer(self):
        return YandexProtobuf(self)
