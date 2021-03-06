import os
import audio
from prettytable import PrettyTable
from recognition import (Pocketsphinx, Snowboy, PocketsphinxConfig, SnowboyConfig,
                         get_common_settings)


def root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _get_pocket_sphinx() -> PocketsphinxConfig:
    base = os.path.join(root(), 'pocketsphinx', 'zero_ru_cont_8k_v3')

    hmm = os.path.join(base, 'zero_ru.cd_semi_4000')  # - mobile?
    # hmm = os.path.join(base, 'zero_ru.cd_cont_4000')
    # hmm = os.path.join(base, 'zero_ru.cd_ptm_4000') - mobile?

    dict = os.path.join(base, 'ru.dic')
    # lm = os.path.join(base, 'ru.lm')
    lm = None
    hotwords = ['алекса', 'алекс', 'аалекса']
    threshold = 1e-20
    sample_rate = 16000
    remove_noise = True
    # all noise marked as SIL => remove_noise = False

    return PocketsphinxConfig(hmm, dict, lm, hotwords, threshold, sample_rate, remove_noise)


def _get_snowboy() -> SnowboyConfig:
    base = os.path.join(root(), 'external', 'snowboy', 'resources')
    resource_path = os.path.join(base, 'common.res')
    model_path = os.path.join(base, 'alexa', 'alexa-avs-sample-app', 'alexa.umdl')
    # model_path = os.path.join(base, 'models', 'jarvis.umdl')

    return SnowboyConfig(resource_path, model_path, sensitivity=2.9, audio_gain=1.0)


class PocketSphinxWrap(Pocketsphinx):
    def __init__(self, config):
        super().__init__(config)
        self.seg = None
        self.mn = config.sample_rate / self.get_frate()
        self.samples = 0

    def get_seg(self):
        return self.seg

    def is_hotword(self, raw_frames) -> bool:
        if not self._is_start:
            self._is_start = True
            self._decoder.start_utt()

        self.samples += (len(raw_frames) // 2)
        self._decoder.process_raw(raw_frames, False, False)
        hypothesis = self._decoder.hyp()

        if hypothesis:
            cnt = 0
            for it in self._decoder.seg():
                if cnt != 0:
                    print("Error seg len")
                start = int(it.start_frame * self.mn)
                end = int(it.end_frame * self.mn)
                dt = end - start
                if cnt == 0:
                    self.seg = [self.samples - dt, self.samples]
                if it.word.strip() != 'алекса':
                    print(it.word)

                cnt += 1

            # for it in self._decoder.seg():
            #     print("{}: {}, {}, {}, {}, {}, {}".format(it.word, it.ascore, it.lscore, it.lback, it.prob, it.start_frame, it.end_frame))

            # if hypothesis.hypstr.find(self._config.hotword) >= 0:
            self._decoder.end_utt()
            self._is_start = False
            return True

        return False


class SnowboyWrap(Snowboy):
    def __init__(self, config):
        super().__init__(config)
        self.seg = None
        self.samples = 0

    def get_seg(self):
        return self.seg

    def is_hotword(self, raw_frames) -> bool:
        self.samples += (len(raw_frames) // 2)
        result = super().is_hotword(raw_frames)

        if result:
            self.seg = [self.samples - 10000, self.samples]

        return result


class TimeRange(object):
    def __init__(self, start, stop):
        self.start = start
        self.stop = stop

    def intersect(self, other):
        return self.stop >= other.start >= self.start or self.stop >= other.stop >= self.start

    def __str__(self):
        return "{}-{}".format(self.start, self.stop)


def calc_intersect(base_arr, data_arr):
    base_ind = 0
    data_ind = 0
    intersect = 0
    while base_ind < len(base_arr) and data_ind < len(data_arr):
        base = base_arr[base_ind]
        data = data_arr[data_ind]
        if base.intersect(data):
            intersect += 1
            base_ind += 1
            data_ind += 1
        else:
            if base.start > data.start:
                data_ind += 1
            else:
                base_ind += 1
    return intersect


class Result(object):
    def __init__(self, sample_rate):
        self.segs = []
        assert sample_rate in [8000, 16000], "Wrong sample_rate"
        self.sample_rate = sample_rate
        self.seg_mn = 16000 // sample_rate

    def add_seg(self, seg):
        self.segs.append(TimeRange(seg[0] * self.seg_mn, seg[1] * self.seg_mn))

    def stat(self, labels):
        success = calc_intersect(labels, self.segs)
        fail = len(self.segs) - success

        success = str(success * 100 / len(labels)) + '%'

        if len(self.segs) == 0:
            fail = '0.0%'
        else:
            fail = str(fail * 100 / len(self.segs)) + '%'

        return success, fail


class Sample(object):
    def __init__(self, device, samples_root):
        self.device = device
        self.file_wav = os.path.join(samples_root, 'audio.wav')
        self.labels = Sample._load_labels(os.path.join(samples_root, 'audio.labels'))

        self.pocket_settings = _get_pocket_sphinx()

        base = os.path.join(root(), 'pocketsphinx', 'zero_ru_cont_8k_v3')
        # self.hmms = [os.path.join(base, 'zero_ru.cd_cont_4000'),
        #              os.path.join(base, 'zero_ru.cd_semi_4000'),
        #              os.path.join(base, 'zero_ru.cd_ptm_4000')]
        self.hmms = [os.path.join(base, 'zero_ru.cd_semi_4000')]
        # self.thresholds = [1e-5, 1e-10, 1e-20, 1e-30, 1e-40, 1e-50]
        self.thresholds = [1e-10, 1e-20, 1e-30, 1e-40, 1e-50]
        # self.remove_noises = [True, False]
        self.remove_noises = [True, False]
        # self.sample_rates = [8000, 16000]
        self.sample_rates = [16000]
        self.results = []

    @staticmethod
    def _load_labels(path):
        return [TimeRange(*[int(it) for it in line.split('-')]) for line in open(path).readlines()]

    def cnt_params(self):
        return (len(self.hmms) * len(self.thresholds) * len(self.remove_noises) *
                len(self.sample_rates))

    def get_hmm(self, ind):
        ind = ind // (len(self.thresholds) * len(self.remove_noises) * len(self.sample_rates))
        return self.hmms[ind % len(self.hmms)]

    def get_threshold(self, ind):
        ind = ind // (len(self.remove_noises) * len(self.sample_rates))
        return self.thresholds[ind % len(self.thresholds)]

    def get_remove_noise(self, ind):
        ind = ind // len(self.sample_rates)
        return self.remove_noises[ind % len(self.remove_noises)]

    def get_sample_rate(self, ind):
        return self.sample_rates[ind % len(self.sample_rates)]

    def check(self):
        frames = 128 # TODO: 10 ms
        cnt = self.cnt_params()
        for ind in range(cnt):
            print("  check: {} of {}".format(ind + 1, cnt))
            self._check_one(self.get_hmm(ind),
                            self.get_threshold(ind),
                            self.get_remove_noise(ind),
                            self.get_sample_rate(ind),
                            frames)

    def _check_one(self, hmm, thresholds, remove_noise, sample_rate, frames_cnt):
        self.pocket_settings.hmm = hmm
        self.pocket_settings.threshold = thresholds
        self.pocket_settings.remove_noise = remove_noise
        self.pocket_settings.sample_rate = sample_rate
        base = os.path.join(root(), 'pocketsphinx', 'zero_ru_cont_8k_v3')
        self.pocket_settings.dict = os.path.join(base, 'ru.dic')

        pocket = PocketSphinxWrap(self.pocket_settings)

        settings = get_common_settings(self.device, None, [pocket.get_audio_settings()])
        wav = audio.AudioData.load_as_wav(self.file_wav, settings)
        mic = self.device.create_data_stream(wav)

        result = Result(sample_rate)
        while True:
            frames = mic.read(frames_cnt)
            if len(frames) == 0:
                break

            if pocket.is_hotword(frames):
                result.add_seg(pocket.get_seg())

        self.results.append(result)

    def show(self):
        print()
        print("{}:".format(self.file_wav))
        t = PrettyTable(['hmm', 'thresholds', 'remove_noise', 'sample_rate', 'success', 'fail'])
        for ind in range(self.cnt_params()):
            hmm = self.get_hmm(ind)
            threshold = self.get_threshold(ind)
            remove_noise = self.get_remove_noise(ind)
            sample_rate = self.get_sample_rate(ind)
            success, fail = self.results[ind].stat(self.labels)
            t.add_row([hmm, threshold, remove_noise, sample_rate, success, fail])
        print(t)


class SampleSnowboy(object):
    def __init__(self, device, samples_root):
        self.device = device
        self.file_wav = os.path.join(samples_root, 'audio.wav')
        self.labels = Sample._load_labels(os.path.join(samples_root, 'audio.labels'))
        self.snowboy_settings = _get_snowboy()

        self.sensitivities = [0.7, 0.8, 0.9, 1.0]
        self.audio_gains = [0.5, 1.0, 1.5, 2.0, 3.0]
        self.results = []

    @staticmethod
    def _load_labels(path):
        return [TimeRange(*[int(it) for it in line.split('-')]) for line in open(path).readlines()]

    def cnt_params(self):
        return len(self.sensitivities) * len(self.audio_gains)

    def get_sensitivity(self, ind):
        ind = ind // len(self.audio_gains)
        return self.sensitivities[ind % len(self.sensitivities)]

    def get_audio_gain(self, ind):
        return self.audio_gains[ind % len(self.audio_gains)]

    def check(self):
        frames = 128 # TODO: 10 ms
        cnt = self.cnt_params()
        for ind in range(cnt):
            print("  check: {} of {}".format(ind + 1, cnt))
            self._check_one(self.get_sensitivity(ind), self.get_audio_gain(ind), frames)

    def _check_one(self, sensitivity, audio_gain, frames_cnt):
        self.snowboy_settings.sensitivity = sensitivity
        self.snowboy_settings.audio_gain = audio_gain

        snowboy = SnowboyWrap(self.snowboy_settings)
        settings = get_common_settings(self.device, None, [snowboy.get_audio_settings()])
        wav = audio.AudioData.load_as_wav(self.file_wav, settings)
        mic = self.device.create_data_stream(wav)

        result = Result(settings.sample_rate)
        while True:
            frames = mic.read(frames_cnt)
            if len(frames) == 0:
                break

            if snowboy.is_hotword(frames):
                result.add_seg(snowboy.get_seg())

        self.results.append(result)

    def show(self):
        print()
        print("{}:".format(self.file_wav))
        t = PrettyTable(['sensitivity', 'audio_gain', 'success', 'fail'])
        for ind in range(self.cnt_params()):
            sensitivity = self.get_sensitivity(ind)
            audio_gain = self.get_audio_gain(ind)
            success, fail = self.results[ind].stat(self.labels)
            t.add_row([sensitivity, audio_gain, success, fail])
        print(t)


def run():
    device = audio.Device()
    try:
        base = os.path.join(root(), 'samples', 'speech')
        samples = [
            SampleSnowboy(device, os.path.join(base, 'commands', 'vladimir')),
            SampleSnowboy(device, os.path.join(base, 'commands', 'masha')),
                   # Sample(device, 'story', 'vladimir'),
                   # Sample(device, 'story', 'masha'),
                   ]

        cnt = len(samples)
        for ind, sample in enumerate(samples):
            print("sample: {} of {}".format(ind + 1, cnt))
            sample.check()

        for sample in samples:
            sample.show()

    except KeyboardInterrupt:
        pass
    finally:
        device.terminate()
