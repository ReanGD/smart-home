from ..stream_settings import StreamSettings


class Recognizer(object):
    def __init__(self, settings):
        self._settings = settings

    def recognize_start(self, data_settings: StreamSettings):
        raise Exception('Not implemented "recognize_start"')

    def recognize_add_frames(self, raw_frames):
        raise Exception('Not implemented "recognize_add_data"')

    def recognize_finish(self):
        raise Exception('Not implemented "recognize_finish"')


class RecognizerSettings(object):
    def create_recognizer(self) -> Recognizer:
        raise Exception('Not implemented "create_recognizer"')

