import atexit

try:
    import _portaudio as pa
except ImportError:
    print("Could not import the PyAudio C module '_portaudio'.")
    raise

pa.initialize()
atexit.register(lambda: pa.terminate())

from .settings import DeviceInfo, AudioSettings, StreamSettings
from .streams import Stream, SettingsConverter, Storage, Microphone, DataStream, WavStream
from .types import *


__all__ = [
    'DeviceInfo',
    'AudioSettings',
    'StreamSettings',
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
