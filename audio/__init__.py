import atexit

try:
    import _portaudio as pa
except ImportError:
    print("Could not import the PyAudio C module '_portaudio'.")
    raise

pa.initialize()
atexit.register(lambda: pa.terminate())

from .audio_data import AudioData
from .stream_settings import StreamSettings
from .streams import Stream, Microphone, DataStream, WavStream
from .types import *


__all__ = [
    'AudioData',
    'StreamSettings',
    'Stream',
    'Microphone',
    'DataStream',
    'WavStream',
    'paFloat32',
    'paInt32',
    'paInt24',
    'paInt16',
    'paInt8',
    'paUInt8',
    'paFormats'
]
