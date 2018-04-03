import pyaudio
import vad_utils
import voice_recognizer as vr
import external.snowboy.snowboydetect as snowboydetect


class Snowboy(vad_utils.VadBase):
    def __init__(self, device, sensitivity=0.5, audio_gain=1.0):
        res = '/home/rean/projects/git/smart-home/external/snowboy/resources/common.res'
        model = ('/home/rean/projects/git/smart-home/external/snowboy/resources/'
                 'alexa/alexa-avs-sample-app/alexa.umdl')
        self._snowboy = vr.SnowboyWrap(res, model, sensitivity, audio_gain)
        self._device = device

    def clone(self):
        return Snowboy(self._device,
                       self._snowboy.get_sensitivity(),
                       self._snowboy.get_audio_gain())

    def get_audio_settings(self):
        return self._snowboy.get_audio_settings(self._device)

    def is_speech(self, frame):
        return self._snowboy.is_speech(frame)


def run(device):
    print('snowboy')
    sensitivity = 0.5  # 0.5
    audio_gain = 1.0  # 1.0
    vad_utils.check_all(device, Snowboy(device, sensitivity, audio_gain))
