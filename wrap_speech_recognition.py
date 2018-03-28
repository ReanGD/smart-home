import speech_recognition as sr


class Wrapper:
    def __init__(self):
        device_index = Wrapper._get_re_speaker_mic_array()
        if device_index is None:
            print("not found re_speaker")
        self._recognizer = sr.Recognizer()
        self._microphone = sr.Microphone(device_index=device_index)

    @staticmethod
    def _get_re_speaker_mic_array():
        for index, name in enumerate(sr.Microphone.list_microphone_names()):
            if name.startswith("ReSpeaker MicArray"):
                return index

        return None

    def loop(self):
        print("Init microphone...")
        with self._microphone as source:
            self._recognizer.adjust_for_ambient_noise(source)

        self._recognizer.energy_threshold += 50
        print("energy_threshold = {}".format(self._recognizer.energy_threshold))
        try:
            while True:
                print("Start listen")
                with self._microphone as source:
                    audio = self._recognizer.listen(source)
                print("Start recognize")
                try:
                    statement = self._recognizer.recognize_google(audio, language="ru_RU")
                    statement = statement.lower()
                    print("Result: {}".format(statement))

                except sr.UnknownValueError:
                    print("Error")
                except sr.RequestError as e:
                    print("Google Speech Recognition error: {0}".format(e))
        except KeyboardInterrupt:
            print("Bay")


def run():
    Wrapper().loop()
