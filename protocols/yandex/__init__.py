import os
import sys

_CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
try:
    if _CURRENT_DIR not in sys.path:
        sys.path.append(_CURRENT_DIR)

    from . import basic_pb2
    from . import tts_pb2
    from . import ttsbackend_pb2
    from . import voiceproxy_pb2

    from .serrialize_protocol import YandexSerrializeProtocol, YandexClient
    from .voiceproxy_pb2 import AddDataResponse
finally:
    sys.path.remove(_CURRENT_DIR)


__all__ = [
    'AddDataResponse',
    'YandexSerrializeProtocol',
    'YandexClient',
]
