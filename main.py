import utils
import record
import hotword_detector
import wrap_speech_recognition


def print_microphones():
    model = '/home/rean/projects/git/smart-home/external/snowboy/resources/alexa/alexa-avs-sample-app/alexa.umdl'
    resource = '/home/rean/projects/git/smart-home/external/snowboy/resources/common.res'

    snowboy = utils.Snowboy(resource, model, sensitivity=1.0, audio_gain=1.0)
    audio = utils.Audio()
    # mic = audio.create_microphone()
    mic = audio.create_microphone_by_snowboy(snowboy)
    for _ in range(10):
        mic.wait_for_hot_word(snowboy)
    audio.terminate()

def run_speech_recognition():
    wrap_speech_recognition.run()


def run_record():
    record.run()


def run_hotword_detector():
    hotword_detector.run()


def main():
     print("start")
     print_microphones()
     # run_speech_recognition()
     # run_record()
     # run_hotword_detector()
     print("stop")


if __name__ == '__main__':
    main()
