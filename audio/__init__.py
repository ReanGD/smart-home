import atexit

try:
    import _portaudio as pa
    pa.initialize()
    atexit.register(pa.terminate)
except ImportError:
    print("Could not import the PyAudio C module '_portaudio'.")
    raise


from .devices import Devices
from .settings import AudioSettings
from .streams import Stream, SettingsConverter, Storage, Microphone, DataStream, WavStream
from .types import PA_UINT8, PA_INT16, PA_INT24, PA_INT32, PA_FORMATS


__all__ = [
    'Devices',
    'AudioSettings',
    'Stream',
    'SettingsConverter',
    'Storage',
    'Microphone',
    'DataStream',
    'WavStream',
    'PA_INT32',
    'PA_INT24',
    'PA_INT16',
    'PA_UINT8',
    'PA_FORMATS'
]
