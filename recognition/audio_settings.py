from pyaudio import paInt16
from typing import List
from audio import StreamSettings, Device


class AudioSettings(object):
    def __init__(self, channels: int=1,
                 sample_format=paInt16,
                 sample_rate: int=16000,
                 frames: int=1024):
        self.channels = channels
        self.sample_format = sample_format
        self.sample_rate = sample_rate
        self.frames = frames


def get_common_settings(device: Device, device_index: int,
                        settings: List[AudioSettings]) -> StreamSettings:
    channels = settings[0].channels
    sample_format = settings[0].sample_format
    sample_rate = settings[0].sample_rate
    for setting in settings:
        if (channels != setting.channels
                or sample_format != setting.sample_format
                or sample_rate != setting.sample_rate):
            raise Exception("Settings are not consistent")

    frames_per_buffer = max(settings, key=lambda s: s.frames).frames
    return StreamSettings(device, device_index, channels, sample_format, sample_rate,
                          frames_per_buffer)
