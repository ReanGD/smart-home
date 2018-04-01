import pyaudio
import external.snowboy.snowboydetect as snowboydetect
import voice_recognizer as vr
import vad_utils


class Snowboy(object):
    def __init__(self, sensitivity=0.5, audio_gain=1.0):
        res = '/home/rean/projects/git/smart-home/external/snowboy/resources/common.res'
        model = ('/home/rean/projects/git/smart-home/external/snowboy/resources/'
                 'alexa/alexa-avs-sample-app/alexa.umdl')
        self._sensitivity = sensitivity
        self._audio_gain = audio_gain
        self._detector = snowboydetect.SnowboyDetect(resource_filename=res.encode(),
                                                     model_str=model.encode())
        self._detector.SetAudioGain(audio_gain)
        num_hotwords = self._detector.NumHotwords()
        self._detector.SetSensitivity(",".join([str(sensitivity)] * num_hotwords).encode())

    def clone(self):
        return Snowboy(self._sensitivity, self._audio_gain)

    def get_audio_settings(self, device, device_index=None):
        channels = self._detector.NumChannels()
        sample_format = pyaudio.get_format_from_width(self._detector.BitsPerSample() / 8)
        sample_rate = self._detector.SampleRate()
        frames_per_buffer = 2048

        return vr.StreamSettings(device, device_index, channels, sample_format,
                                            sample_rate, frames_per_buffer)

    def run_detection(self, frame):
        snowboy_result = self._detector.RunDetection(frame)
        assert snowboy_result != -1, "Error initializing streams or reading audio data"
        if snowboy_result == -2:
            return False
        elif snowboy_result == 0:
            return True
        else:
            print('voice found')
            return True


def run():
    print('snowboy')
    sensitivity = 0.5  # 0.5
    audio_gain = 1.0  # 1.0
    vad_utils.check_all(Snowboy(sensitivity, audio_gain))
