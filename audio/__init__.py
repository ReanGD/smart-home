import atexit

try:
    import _portaudio as pa
except ImportError:
    print("Could not import the PyAudio C module '_portaudio'.")
    raise

pa.initialize()
atexit.register(lambda: pa.terminate())

from .devices import Devices
from .settings import AudioSettings
from .streams import Stream, SettingsConverter, Storage, Microphone, DataStream, WavStream
from .types import *


__all__ = [
    'Devices',
    'AudioSettings',
    'Stream',
    'SettingsConverter',
    'Storage',
    'Microphone',
    'DataStream',
    'WavStream',
    'paInt32',
    'paInt24',
    'paInt16',
    'paUInt8',
    'paFormats'
]
