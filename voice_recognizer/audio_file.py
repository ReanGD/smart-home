import wave
import pyaudio
from voice_recognizer.stream_settings import StreamSettings
from voice_recognizer.audio_data import AudioData


class AudioFile(object):
    @staticmethod
    def read_wav(file, out_settings: StreamSettings):
        wav_reader = wave.open(file, "rb")
        try:
            sample_format = pyaudio.get_format_from_width(wav_reader.getsampwidth())
            in_settings = StreamSettings(out_settings.device,
                                         channels = wav_reader.getnchannels(),
                                         sample_rate = wav_reader.getframerate(),
                                         sample_format = sample_format)
            raw_data = wav_reader.readframes(wav_reader.getnframes())
            return AudioData(raw_data, in_settings).get_raw_data(out_settings)
        finally:
            wav_reader.close()
