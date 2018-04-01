import pyaudio
import vad_utils
import webrtcvad
import voice_recognizer as vr


class VadWrap(object):
    def __init__(self, mode, sample_rate):
        self._vad = webrtcvad.Vad()
        self._vad.set_mode(mode)
        self._mode = mode
        self._sample_rate = sample_rate
        self._frames_read = 0

    def clone(self):
        return VadWrap(self._mode, self._sample_rate)

    def set_frames_read(self, frames_read):
        self._frames_read = frames_read

    def get_audio_settings(self, device, device_index=None):
        return vr.StreamSettings(device,
                                 device_index=device_index,
                                 sample_format=pyaudio.paInt16,
                                 frames_per_buffer=1024)

    def is_speech(self, frames):
        return self._vad.is_speech(frames, self._sample_rate)


def run():
    print('webrtcvad')
    vad_utils.check_all(VadWrap(3, 16000))

