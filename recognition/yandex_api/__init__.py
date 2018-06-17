import os
import sys

current_dir = os.path.dirname(os.path.realpath(__file__))

if current_dir not in sys.path:
    sys.path.append(current_dir)

from . import basic_pb2
from . import tts_pb2
from . import ttsbackend_pb2
from . import voiceproxy_pb2

sys.path.remove(current_dir)