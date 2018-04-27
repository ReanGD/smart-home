from experiments import vad_utils
import audio as vr
import config


class Snowboy(vad_utils.VadBase):
    def __init__(self, device, cfg):
        self._snowboy = vr.SnowboyWrap(cfg)
        self._device = device

    def clone(self):
        return Snowboy(self._device, self._snowboy.get_config())

    def get_audio_settings(self):
        return self._snowboy.get_audio_settings(self._device)

    def is_speech(self, frame):
        return self._snowboy.is_speech(frame)


def run(device):
    print('snowboy')
    cfg = config.snowboy
    vad_utils.check_all(device, Snowboy(device, cfg))
