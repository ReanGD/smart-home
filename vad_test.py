import pyaudio
import audioop
import vad_utils
import voice_recognizer as vr


class VadTest(object):
    def __init__(self, settings: vr.StreamSettings, dynamic_energy_threshold):
        self._settings = settings
        self._seconds_per_buffer = 0
        self._dynamic_energy_threshold = dynamic_energy_threshold
        self._ind = 0
        self._energy_threshold = 300  # minimum audio energy to consider for recording

    def clone(self):
        return VadTest(self._settings, self._dynamic_energy_threshold)

    def set_frames_read(self, frames_read):
        self._seconds_per_buffer = float(frames_read) / self._settings.sample_rate

    def get_audio_settings(self, device, device_index=None):
        return vr.StreamSettings(device,
                                 device_index=device_index,
                                 channels=self._settings.channels,
                                 sample_rate=self._settings.sample_rate,
                                 sample_format=self._settings.sample_format,
                                 frames_per_buffer=1024)

    def calc_energy(self, frames):
        # Return the root-mean-square of the fragment, i.e. sqrt(sum(S_i^2)/n).
        return audioop.rms(frames, self._settings.sample_width)  # energy of the audio signal

    def update_energy_threshold(self, energy):
        dynamic_energy_adjustment_damping = 0.15
        dynamic_energy_ratio = 1.5

        # dynamically adjust the energy threshold using asymmetric weighted average
        damping = dynamic_energy_adjustment_damping ** self._seconds_per_buffer  # account for different chunk sizes and rates
        target_energy = energy * dynamic_energy_ratio
        self._energy_threshold = self._energy_threshold * damping + target_energy * (1 - damping)

    def is_speech(self, frames):
        # frame = 10 ms
        energy = self.calc_energy(frames)

        if self._ind * 10 <= 1000:
            self.update_energy_threshold(energy)
            self._ind += 1
            return False

        if energy > self._energy_threshold:
            return True

        if self._dynamic_energy_threshold:
            self.update_energy_threshold(energy)

        return False


def run():
    print('test')
    device = vr.Device()
    settings = vr.StreamSettings(device,
                                 device_index=None,
                                 channels=1,
                                 sample_format=pyaudio.paInt16,
                                 frames_per_buffer=1024)
    device.terminate()
    dynamic_energy_threshold = True
    vad_utils.check_all(VadTest(settings, dynamic_energy_threshold))

