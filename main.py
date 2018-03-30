import record
import hotword_detector
import wrap_speech_recognition


def run_speech_recognition():
    wrap_speech_recognition.run()


def run_record():
    record.run()


def run_hotword_detector():
    hotword_detector.run()


def main():
     print("start")
     # run_speech_recognition()
     # run_record()
     run_hotword_detector()
     print("stop")


if __name__ == '__main__':
    main()
