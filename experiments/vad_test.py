import pyaudio
import audioop
from experiments import vad_utils
import numpy as np
import audio as vr
import matplotlib.pyplot as plt


class VadTest(vad_utils.VadBase):
    def __init__(self, settings: vr.StreamSettings, dynamic_energy_threshold):
        self._settings = settings
        self._seconds_per_buffer = 0
        self._dynamic_energy_threshold = dynamic_energy_threshold
        self._energy_threshold = 300  # minimum audio energy to consider for recording
        self._frame_ind = 0
        self._wave_ind = 0

        self._graph_name = ''
        self._graph_frame_x = []
        self._graph_wave_x = []
        self._graph_wave = []
        self._graph_energy = []
        self._graph_test = []
        self._graph_energy_threshold = []

    def clone(self):
        return VadTest(self._settings, self._dynamic_energy_threshold)

    def init(self, frames_read, path):
        self._graph_name = path
        self._seconds_per_buffer = float(frames_read) / self._settings.sample_rate

    def get_audio_settings(self):
        return self._settings

    def _calc_energy(self, frames):
        # Return the root-mean-square of the fragment, i.e. sqrt(sum(S_i^2)/n).
        return audioop.rms(frames, self._settings.sample_width)  # energy of the audio signal

    def _update_energy_threshold(self, energy):
        dynamic_energy_adjustment_damping = 0.15
        dynamic_energy_ratio = 1.5

        # dynamically adjust the energy threshold using asymmetric weighted average
        damping = dynamic_energy_adjustment_damping ** self._seconds_per_buffer  # account for different chunk sizes and rates
        target_energy = energy * dynamic_energy_ratio
        self._energy_threshold = self._energy_threshold * damping + target_energy * (1 - damping)

    def is_speech(self, frames):
        # frame = 10 ms
        energy = self._calc_energy(frames)
        self._graph_energy.append(energy)

        buf = np.frombuffer(frames, dtype=np.int16)
        res = 0
        for it in buf:
            res += it
            if self._wave_ind % 10 == 9:
                self._graph_wave_x.append(self._wave_ind)
                self._graph_wave.append(res / 10.0)
                res = 0
            self._wave_ind += 1
        # val = math.sqrt(sum([int(it) * int(it) for it in buf]) / len(buf))
        # self._graph_wave.append(val)
        self._graph_frame_x.append(self._wave_ind)

        result = False
        if self._frame_ind * 10 <= 1000:
            self._update_energy_threshold(energy)
        else:
            if energy > self._energy_threshold:
                result = True
            elif self._dynamic_energy_threshold:
                self._update_energy_threshold(energy)

        self._graph_energy_threshold.append(self._energy_threshold)
        self._frame_ind += 1
        return result

    def close(self):
        # plt.plot(self._graph_energy_threshold, 'b-')

        plt.figure(1, dpi=200)

        sp = plt.subplot(211)
        plt.title(self._graph_name)
        plt.plot(self._graph_wave_x, self._graph_wave, 'b-', linewidth=0.4)
        plt.axis([0, self._wave_ind, min(self._graph_wave), max(self._graph_wave)])
        sp.xaxis.set_visible(False)
        sp.yaxis.set_visible(False)

        sp = plt.subplot(212)
        plt.plot(self._graph_frame_x, self._graph_energy, 'r-', linewidth=0.6)
        plt.axis([0, self._wave_ind, min(self._graph_energy), max(self._graph_energy)], 'off')
        sp.xaxis.set_visible(False)
        sp.yaxis.set_visible(False)

        # plt.yscale('log')
        plt.show()


def run(device):
    print('test')
    settings = vr.StreamSettings(device,
                                 device_index=None,
                                 channels=1,
                                 sample_format=pyaudio.paInt16,
                                 frames_per_buffer=1024)

    dynamic_energy_threshold = True
    path = None
    # path = 'samples/voice.wav'
    # path = 'samples/voice_music_8.wav'
    vad_utils.check_all(device, VadTest(settings, dynamic_energy_threshold), path)
