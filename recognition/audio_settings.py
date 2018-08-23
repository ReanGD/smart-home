from typing import List
from audio import AudioSettings


def get_common_settings(settings: List[AudioSettings]) -> AudioSettings:
    channels = settings[0].channels
    sample_format = settings[0].sample_format
    sample_rate = settings[0].sample_rate
    for setting in settings:
        if (channels != setting.channels
                or sample_format != setting.sample_format
                or sample_rate != setting.sample_rate):
            raise Exception("Settings are not consistent")

    return settings[0]
