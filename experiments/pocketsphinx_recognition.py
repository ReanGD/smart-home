import os
import audio
from pocketsphinx.pocketsphinx import Decoder


def root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def speech_root():
    return os.path.join(root(), 'samples', 'speech')


def create_decoder():
    base = os.path.join(root(), 'pocketsphinx', 'zero_ru_cont_8k_v3')
    hmm = os.path.join(base, 'zero_ru.cd_semi_4000')  # - mobile?
    # hmm = os.path.join(base, 'zero_ru.cd_cont_4000')
    # hmm = os.path.join(base, 'zero_ru.cd_ptm_4000') - mobile?

    dict = os.path.join(base, 'ru.dic.orig')
    # dict = os.path.join(base, 'ru.dic')
    lm = os.path.join(base, 'ru.lm.orig')

    # kws = os.path.join(base, 'ru.dic.orig.keywords')
    kws = os.path.join(base, 'keywords.mini')

    decoder_config = Decoder.default_config()
    decoder_config.set_string('-hmm', hmm)

    # decoder_config.set_string("-lm", lm)
    # decoder_config.set_string('-keyphrase', 'алекса')
    # decoder_config.set_float('-kws_threshold', 1e-20)
    decoder_config.set_string('-kws', kws)

    decoder_config.set_string('-dict', dict)
    decoder_config.set_boolean('-remove_noise', False)
    decoder_config.set_float('-samprate', 8000)
    decoder_config.set_string('-logfn', os.devnull)

    decoder = Decoder(decoder_config)

    return decoder


def decode(device, decoder, wav_path):
    print('{}:'.format(wav_path))
    settings = audio.StreamSettings(device, device_index=None, sample_rate=8000)
    wav = audio.AudioData.load_as_wav(wav_path, settings)
    mic = device.create_data_stream(wav)

    decoder.start_utt()
    while True:
        frames = mic.read(128)
        if len(frames) == 0:
            break
        decoder.process_raw(frames, False, False)

    print([it.word for it in decoder.seg()])
    print([(h.hypstr, h.score) for h, i in zip(decoder.nbest(), range(10))])

    decoder.end_utt()


def run():
    wav_dir = os.path.join(speech_root(), 'commands', 'masha', '16000')


    device = audio.Device()
    decoder = create_decoder()
    try:
        for ind in range(20):
            decode(device, decoder, wav_path = os.path.join(wav_dir, str(ind) + '.wav'))
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
    finally:
        device.terminate()
