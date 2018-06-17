import logging
import asyncio
from sys import stdout
from audio import StreamSettings, paInt16
from .audio_settings import AudioSettings
from .yandex_api.basic_pb2 import ConnectionResponse
from .base import PhraseRecognizer, PhraseRecognizerConfig
from .yandex_api.voiceproxy_pb2 import ConnectionRequest, AddData, AddDataResponse, AdvancedASROptions
from .yandex_api.transport import Transport


logger = logging.getLogger('yandex_protobuf')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(stdout)
logger.addHandler(handler)


class YandexProtobufError(RuntimeError):
    def __init__(self, message):
        RuntimeError.__init__(self, message)


class Connection(object):
    def __init__(self, config):
        self._config = config
        self._transport = Transport()
        self._recv_task = None

    async def connect(self, result_callback, finish_result_callback):
        app, host, port = self._config.app, self._config.host, self._config.port
        await self._transport.connect(host, port)
        await self._transport.upgrade_connection(app, host, port)
        await self._send_connection_request()
        self._recv_task = asyncio.ensure_future(
            self._recv_loop(result_callback, finish_result_callback))

    @staticmethod
    def _process_recognition(recognition):
        if len(recognition) != 1:
            raise YandexProtobufError('len(recognition) != 1')

        phrase = recognition[0]
        if phrase.confidence != 1.0:
            raise YandexProtobufError('phrase.confidence != 1')
        elif len(phrase.words) != 1:
            raise YandexProtobufError('len(words) != 1')

        word = phrase.words[0]
        if word.confidence != 1.0:
            raise YandexProtobufError('word.confidence != 1')

        return word.value

    async def _recv_loop(self, result_callback, finish_result_callback):
        last_text = ''
        while True:
            response = await self._transport.recv_protobuf(AddDataResponse, ConnectionResponse)

            if isinstance(response, ConnectionResponse):
                raise Connection._error_from_response(response,
                                                      'Bad AddData response (wrong type)')
            elif response is None:
                raise YandexProtobufError('Bad AddData response (null result)')
            elif response.responseCode != 200:
                raise Connection._error_from_response(response,
                                                      'Bad AddData response (responce code)')

            if len(response.recognition) == 0:
                continue

            if response.endOfUtt:
                await finish_result_callback(response)

            text = Connection._process_recognition(response.recognition)
            if last_text != text:
                last_text = text
                await result_callback(text)

    async def add_data(self, data):
        if data is None:
            await self._transport.send_protobuf(AddData(lastChunk=True))
        else:
            await self._transport.send_protobuf(AddData(lastChunk=False, audioData=data))

    @staticmethod
    def _error_from_response(response, text):
        error_text = '{}, status_code={}'.format(text, response.responseCode)
        if response.HasField("message"):
            error_text += ', message is "{}"'.format(response.message)
        return YandexProtobufError(error_text)

    async def _send_connection_request(self):
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

        logger.debug('Starting a request for a connection')
        await self._transport.send_protobuf(request)
        response = await self._transport.recv_protobuf(ConnectionResponse)

        if response.responseCode != 200:
            raise Connection._error_from_response(response, 'Wrong response from server')

    def close(self):
        if self._transport is not None:
            self._recv_task.cancel()
            self._recv_task = None
            self._transport.close()
            self._transport = None


class YandexProtobuf(PhraseRecognizer):
    def __init__(self, config):
        super().__init__(config)
        self._data_settings = None
        self._conn = None
        self._audio_settings = AudioSettings(channels=1, sample_format=paInt16, sample_rate=16000)
        self._connection = None

    def get_audio_settings(self) -> AudioSettings:
        return self._audio_settings

    async def _recv_result(self, text):
        print(text)

    async def _recv_finish_result(self, response):
        if len(response.recognition) != 0:
            for bio in response.bioResult:
                print('{} {} {}'.format(bio.classname, bio.confidence, bio.tag))

        for ind, phrase in enumerate(response.recognition):
            words = ['{}({})'.format(word.value, word.confidence) for word in phrase.words]
            print('{}: {}'.format(ind, ':'.join(words)))

    async def _recognize_start(self, data_settings: StreamSettings):
        self._data_settings = data_settings
        self._connection = Connection(self.get_config())
        await self._connection.connect(self._recv_result, self._recv_finish_result)

    async def _add_data(self, data):
        await self._connection.add_data(data)

    def recognize_finish(self):
        pass

    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None


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
