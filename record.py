import pyaudio
import wave


FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
CHUNK = 2048


class Mic(object):
    def __init__(self):
        self.audio = None
        self.stream_in = None

    def record(self, seconds):
        self.audio = pyaudio.PyAudio()
        self.stream_in = self.audio.open(format=FORMAT, channels=CHANNELS,
                                         rate=RATE, input=True,
                                         frames_per_buffer=CHUNK)

        print("recording...")
        frames = []
        for i in range(0, int(RATE / CHUNK * seconds)):
            data = self.stream_in.read(CHUNK)
            frames.append(data)
        print("finished recording")

        self.stream_in.stop_stream()
        self.stream_in.close()
        self.audio.terminate()
        return frames

    def write(self, frames, file):
        waveFile = wave.open(file, 'wb')
        waveFile.setnchannels(CHANNELS)
        waveFile.setsampwidth(self.audio.get_sample_size(FORMAT))
        waveFile.setframerate(RATE)
        waveFile.writeframes(b''.join(frames))
        waveFile.close()


def run():
    mic = Mic()
    frames = mic.record(3)
    mic.write(frames, "file.wav")
