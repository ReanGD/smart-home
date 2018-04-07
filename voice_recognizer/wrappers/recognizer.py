from voice_recognizer.audio_data import AudioData


class Recognizer(object):
    def __init__(self, settings):
        self._settings = settings

    def recognize(self, audio_date: AudioData):
        raise Exception('Not implemented "audio_date"')


class RecognizerSettings(object):
    def create_recognizer(self) -> Recognizer:
        raise Exception('Not implemented "create_recognizer"')





