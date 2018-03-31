import math
import time
import pyaudio
import audioop
import collections
import external.snowboy.snowboydetect as snowboydetect


class Audio(object):
    def __init__(self):
        self._audio = pyaudio.PyAudio()
        self._microphones = []

    @staticmethod
    def print_microphone_info(device_info):
        print(device_info["name"])
        for ind, name in device_info.items():
            print("{}: {}".format(ind, name))

    def print_microphones_info(self):
        Audio.print_microphone_info(self._audio.get_default_input_device_info())

        for i in range(self._audio.get_device_count()):
            self._audio.get_default_input_device_info()
            device_info = self._audio.get_device_info_by_index(i)
            if device_info["maxInputChannels"] != 0:
                print()
                Audio.print_microphone_info(device_info)

    def find_device_info(self, name_start_with):
        for i in range(self._audio.get_device_count()):
            device_info = self._audio.get_device_info_by_index(i)
            if device_info["name"].startswith(name_start_with):
                return i

        return None

    def create_microphone(self, device_index=None):
        count = self._audio.get_device_count()
        if device_index is not None:
            msg = ("Device index out of range ({} devices available; "
                   "device index should be between 0 and {} inclusive)")
            assert 0 <= device_index < count, msg.format(count, count - 1)
            device_info = self._audio.get_device_info_by_index(device_index)
        else:
            device_info = self._audio.get_default_input_device_info()

        sample_rate = device_info.get("defaultSampleRate")
        msg = "Invalid device info returned from PyAudio: {}"
        assert isinstance(sample_rate, (float, int)) and sample_rate > 0, msg.format(device_info)

        channels = 1
        sample_rate = int(sample_rate)  # sampling rate in Hertz
        sample_format = pyaudio.paInt16  # 16-bit size of each sample
        frames_per_buffer = 1024  # number of frames stored in each buffer

        mic = Microphone(self._audio, device_index, channels, sample_format,
                         sample_rate, frames_per_buffer)
        self._microphones.append(mic)
        return mic

    def create_microphone_by_snowboy(self, snowboy, device_index=None):
        count = self._audio.get_device_count()
        if device_index is not None:
            msg = ("Device index out of range ({} devices available; "
                   "device index should be between 0 and {} inclusive)")
            assert 0 <= device_index < count, msg.format(count, count - 1)

        sample_rate = snowboy.sample_rate  # sampling rate in Hertz
        sample_format = snowboy.sample_format  # size of each sample
        channels = snowboy.channels
        frames_per_buffer = 2048  # number of frames stored in each buffer
        mic = Microphone(self._audio, device_index, channels, sample_format,
                         sample_rate, frames_per_buffer)
        self._microphones.append(mic)
        return mic

    def terminate(self):
        for mic in self._microphones:
            mic.close()

        self._audio.terminate()


class Snowboy(object):
    def __init__(self, resource_filename, model_filename, sensitivity=0.5, audio_gain=1.0):
        self._detector = snowboydetect.SnowboyDetect(resource_filename=resource_filename.encode(),
                                                     model_str=model_filename.encode())
        self._detector.SetAudioGain(audio_gain)
        num_hotwords = self._detector.NumHotwords()
        self._detector.SetSensitivity(",".join([str(sensitivity)] * num_hotwords).encode())

    @property
    def sample_rate(self):
        return self._detector.SampleRate()

    @property
    def sample_format(self):
        return pyaudio.get_format_from_width(self._detector.BitsPerSample() / 8)

    @property
    def channels(self):
        return self._detector.NumChannels()

    def run_detection(self, frame):
        return self._detector.RunDetection(frame)


class RingBuffer(object):
    def __init__(self, size=4096):
        self._buf = collections.deque(maxlen=size)

    def extend(self, data):
        self._buf.extend(data)

    def get(self):
        return bytes(bytearray(self._buf))

    def clear(self):
        self._buf.clear()


class Microphone(object):
    def __init__(self, audio, device_index, channels, sample_format,
                 sample_rate, frames_per_buffer):
        self._sample_rate = sample_rate
        self._frames_per_buffer = frames_per_buffer
        self._sample_width = pyaudio.get_sample_size(sample_format)  # size of each sample
        self._ring_buffer = RingBuffer(65536)
        # RingBuffer(channels * self._sample_rate * 5)

        # callback = None
        callback = self.audio_callback
        self._stream_in = audio.open(input_device_index=device_index, channels=channels,
                                     format=sample_format, rate=sample_rate,
                                     frames_per_buffer=frames_per_buffer, input=True,
                                     stream_callback=callback)

    def audio_callback(self, in_data, frame_count, time_info, status):
        self._ring_buffer.extend(in_data)
        play_data = chr(0) * len(in_data)
        return play_data, pyaudio.paContinue

    def wait_for_hot_word(self, snowboy):
        while True:
            data = self._ring_buffer.get()
            if len(data) == 0:
                sleep_time = 0.03
                time.sleep(sleep_time)
                continue

            print(len(data))
            # snowboy_result = snowboy.run_detection(data)
            # assert snowboy_result != -1, "Error initializing streams or reading audio data"
            # if snowboy_result > 0:
            #     self._ring_buffer.clear()
            #     print('wake word found')
            #     break  # wake word found

        print('exit')

    def wait_for_hot_word2(self, snowboy):
        seconds_per_buffer = float(self._frames_per_buffer) / self._sample_rate
        five_seconds_buffer_count = int(math.ceil(2 / seconds_per_buffer))
        print(five_seconds_buffer_count)
        frames = collections.deque(maxlen=five_seconds_buffer_count)
        while True:
            buffer = self._stream_in.read(self._frames_per_buffer, exception_on_overflow=False)
            if len(buffer) == 0:
                print('reached end of the stream')
                break  # reached end of the stream
            frames.append(buffer)
            data = b"".join(frames)
            print(len(data))
            snowboy_result = snowboy.run_detection(data)
            assert snowboy_result != -1, "Error initializing streams or reading audio data"
            if snowboy_result > 0:
                print('wake word found')
                break  # wake word found

        print('exit')


    def wait_for_hot_word3(self, snowboy):
        # snowboy_sample_rate = snowboy.sample_rate
        seconds_per_buffer = float(self._frames_per_buffer) / self._sample_rate
        # resampling_state = None

        # buffers capable of holding 5 seconds of original and resampled audio
        five_seconds_buffer_count = int(math.ceil(2 / seconds_per_buffer))
        print(five_seconds_buffer_count)
        frames = collections.deque(maxlen=five_seconds_buffer_count)
        # resampled_frames = collections.deque(maxlen=five_seconds_buffer_count)
        while True:
            buffer = self._stream_in.read(self._frames_per_buffer, exception_on_overflow=False)
            if len(buffer) == 0:
                print('reached end of the stream')
                break  # reached end of the stream
            # print(len(buffer), self._frames_per_buffer)
            frames.append(buffer)

            # resample audio to the required sample rate
            # resampled_buffer, resampling_state = audioop.ratecv(buffer, self._sample_width, 1,
            #                                                     self._sample_rate,
            #                                                     snowboy_sample_rate,
            #                                                     resampling_state)
            # resampled_frames.append(resampled_buffer)

            # run Snowboy on the resampled audio
            # snowboy_result = snowboy.run_detection(b"".join(resampled_frames))
            data = b"".join(frames)
            print(len(data))
            snowboy_result = snowboy.run_detection(data)
            assert snowboy_result != -1, "Error initializing streams or reading audio data"
            if snowboy_result > 0:
                print('wake word found')
                break  # wake word found

        print('exit')
        # return b"".join(frames)

    def close(self):
        try:
            if not self._stream_in.is_stopped():
                self._stream_in.stop_stream()
        finally:
            self._stream_in.close()
