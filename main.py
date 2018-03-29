import wrap_speech_recognition
import record


def speech_recognition():
    wrap_speech_recognition.run()


def mic_record():
    record.run()


def main():
     print("start")
     # speech_recognition()
     mic_record()
     print("stop")


if __name__ == '__main__':
    main()
