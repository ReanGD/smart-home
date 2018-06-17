import asyncio
from logging import getLogger
from .transport import Transport
from .basic_pb2 import ConnectionResponse
from .voiceproxy_pb2 import ConnectionRequest, AddData, AddDataResponse, AdvancedASROptions


logger = getLogger('yandex_api')


class YandexApiError(RuntimeError):
    def __init__(self, message):
        RuntimeError.__init__(self, message)


def error_from_response(response, text):
    error_text = '{}, status_code={}'.format(text, response.responseCode)
    if response.HasField("message"):
        error_text += ', message is "{}"'.format(response.message)
    return YandexApiError(error_text)


class Api(object):
    def __init__(self):
        self._transport = Transport()
        self._recv_task = None

    async def connect(self, app, host, port, user_uuid, api_key, topic, lang, disable_antimat):
        logger.info('Start connecting to %s:%d', host, port)
        await self._transport.connect(host, port)
        await self._transport.upgrade_connection(app, host, port)
        await self._send_connection_request(user_uuid, api_key, app, topic, lang, disable_antimat)
        logger.info('Connected to %s:%s', host, port)

    def is_active(self):
        return self._transport is not None and self._transport.is_active()

    async def send_audio_data(self, data):
        if data is None:
            logger.debug('Start send finished audio data chank')
            await self._transport.send_protobuf(AddData(lastChunk=True))
        else:
            logger.debug('Start send audio data (%d)', len(data))
            await self._transport.send_protobuf(AddData(lastChunk=False, audioData=data))

    async def recv_loop(self, callback):
        is_continue = True
        try:
            while is_continue:
                response = await self._transport.recv_protobuf(AddDataResponse, ConnectionResponse)

                if isinstance(response, ConnectionResponse):
                    raise error_from_response(response, 'Bad AddData response (wrong type)')
                elif response is None:
                    raise YandexApiError('Bad AddData response (null result)')
                elif response.responseCode != 200:
                    raise error_from_response(response, 'Bad AddData response (responce code)')

                if len(response.recognition) == 0:
                    continue

                logger.debug('Received AddDataResponse')
                is_continue = await callback(response)
        except asyncio.TimeoutError:
            pass
        finally:
            self._recv_task = None
            logger.info('recv loop finished')

    async def recv_loop_run(self, callback):
        if self._recv_task is None:
            self._recv_task = asyncio.ensure_future(self.recv_loop(callback))

    async def _send_connection_request(self, user_uuid, api_key, app, topic, lang, disable_antimat):
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
            uuid=user_uuid,
            apiKey=api_key,
            applicationName=app,
            device='desktop',
            coords='0, 0',
            topic=topic,
            lang=lang,
            format='audio/x-pcm;bit=16;rate=16000',
            punctuation=True,
            disableAntimatNormalizer=disable_antimat,
            advancedASROptions=advanced_asr_options
        )

        logger.debug('Starting a request for a connection')
        await self._transport.send_protobuf(request)
        response = await self._transport.recv_protobuf(ConnectionResponse)

        if response.responseCode != 200:
            raise error_from_response(response, 'Wrong response from server')
        logger.debug('Received a response to the connection request')

    def close(self):
        if self._recv_task is not None:
            asyncio.wait_for(self._recv_task, 1.0)
            self._recv_task = None

        if self.is_active():
            self._transport.close()

        logger.info('Api closed')
