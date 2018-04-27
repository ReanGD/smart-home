import pyaudio
import vad_utils
import webrtcvad
import audio as vr


class VadWrap(vad_utils.VadBase):
    def __init__(self, settings, mode):
        self._vad = webrtcvad.Vad()
        self._vad.set_mode(mode)
        self._mode = mode
        self._settings = settings

    def clone(self):
        return VadWrap(self._settings, self._mode)

    def get_audio_settings(self):
        return self._settings

    def is_speech(self, frames):
        return self._vad.is_speech(frames, self._settings.sample_rate)


def run(device):
    print('webrtcvad')
    settings = vr.StreamSettings(device,
                                 device_index=None,
                                 sample_format=pyaudio.paInt16,
                                 frames_per_buffer=1024)

    vad_utils.check_all(device, VadWrap(settings, mode=3))

