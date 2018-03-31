import wave
import time
import pyaudio
import collections
import external.snowboy.snowboydetect as snowboydetect


class RingBuffer(object):
    def __init__(self, size=4096):
        self._buf = collections.deque(maxlen=size)

    def extend(self, data):
        self._buf.extend(data)

    def get(self):
        tmp = bytes(bytearray(self._buf))
        self._buf.clear()
        return tmp


class HotwordDetector(object):
    def __init__(self, decoder_model, resource, sensitivity):
        self.audio = None
        self.stream_in = None

        self.detector = snowboydetect.SnowboyDetect(resource_filename=resource.encode(),
                                                    model_str=decoder_model.encode())
        self.detector.SetAudioGain(1.0)
        self.num_hotwords = self.detector.NumHotwords()
        # assert self.num_hotwords == 1, "self.num_hotwords == 1"
        # self.detector.SetSensitivity((str(sensitivity)+","+str(sensitivity)).encode())
        self.detector.SetSensitivity((str(sensitivity)).encode())
        self.ring_buffer = RingBuffer(self.detector.NumChannels() * self.detector.SampleRate() * 5)

    def audio_callback(self, in_data, frame_count, time_info, status):
        self.ring_buffer.extend(in_data)
        play_data = chr(0) * len(in_data)
        return play_data, pyaudio.paContinue

    def start(self, seconds):
        self.audio = pyaudio.PyAudio()
        self.format = self.audio.get_format_from_width(self.detector.BitsPerSample() / 8)
        self.channels = self.detector.NumChannels()
        self.rate = self.detector.SampleRate()
        frames_per_buffer = 2048
        print("format = {}, channels = {}, rate = {}".format(self.format, self.channels, self.rate))

        self.stream_in = self.audio.open(input=True, output=False,
                                         format=self.format,
                                         channels=self.channels,
                                         rate=self.rate,
                                         frames_per_buffer=frames_per_buffer,
                                         stream_callback=self.audio_callback)

        print("recording...")

        ind = 0
        frames = []
        state = "PASSIVE"
        silent_count_threshold = 15
        last_status = -10
        while ind != 10000:
            data = self.ring_buffer.get()
            if len(data) == 0:
                sleep_time = 0.03
                time.sleep(sleep_time)
                continue

            status = self.detector.RunDetection(data)
            if status == -1:
                print("Error initializing streams or reading audio data")
            elif status == -2:
                if last_status != status:
                    print('silent')
            elif status == 0:
                print('voice')
            else:
                print(status)

            last_status = status

            # frames.append(data)
            if state == "PASSIVE":
                if status > 0:
                    print("detect!!! status = " + str(status))
                    state = "ACTIVE"
                    silentCount = 0
                    stopRecording = False
            elif state == "ACTIVE":
                if status == -2:  # silence found
                    if silentCount > silent_count_threshold:
                        stopRecording = True
                    else:
                        silentCount = silentCount + 1
                elif status == 0:  # voice found
                    silentCount = 0

                if stopRecording == True:
                    print("wait")
                    state = "PASSIVE"

            ind += 1

        print("writing...")
        # self.write(frames, "file.wav")
        print("stop...")
        #
        # frames = []
        # for i in range(0, int(self.rate / frames_per_buffer * seconds)):
        #     data = self.stream_in.read(frames_per_buffer)
        #     frames.append(data)
        # print("finished recording")

    def terminate(self):
        self.stream_in.stop_stream()
        self.stream_in.close()
        self.audio.terminate()

    def write(self, frames, file):
        waveFile = wave.open(file, 'wb')
        waveFile.setnchannels(self.channels)
        waveFile.setsampwidth(self.audio.get_sample_size(self.format))
        waveFile.setframerate(self.rate)
        waveFile.writeframes(b''.join(frames))
        waveFile.close()


def run():
    model = '/home/rean/projects/git/smart-home/external/snowboy/resources/models/snowboy.umdl'
    # model = '/home/rean/projects/git/smart-home/activate_model/Chewbacca.pmdl'
    model = '/home/rean/projects/git/smart-home/external/snowboy/resources/alexa/alexa-avs-sample-app/alexa.umdl'
    # model = '/home/rean/projects/git/smart-home/external/snowboy/resources/models/jarvis.umdl'
    resource = '/home/rean/projects/git/smart-home/external/snowboy/resources/common.res'
    obj = HotwordDetector(model, resource, sensitivity=1.0)
    try:
        obj.start(5)
    except KeyboardInterrupt:
        obj.terminate()
        print('close')
