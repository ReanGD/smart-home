import os
import audio


def speech_root():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, 'samples', 'speech')


def load_labels(path):
    return [[int(it) for it in line.split('-')] for line in open(path).readlines()]


def write(raw, settings, labels, out_dir):
    for ind, it in enumerate(labels):
        start = it[0] * settings.sample_width
        stop = it[1] * settings.sample_width
        if settings.sample_rate == 8000:
            start //= 2
            stop //= 2
        start &= ~1
        stop &= ~1
        out_path = os.path.join(out_dir, "{}.wav".format(ind))
        audio.AudioData(raw[start:stop], settings).save_as_wav(out_path)


def run():
    sample_rate = 8000
    root = os.path.join(speech_root(), 'commands', 'vladimir')

    labels_path = os.path.join(root, 'audio.labels')
    in_path = os.path.join(root, 'audio.wav')
    out_dir = os.path.join(root, str(sample_rate))

    device = audio.Device()
    try:
        settings = audio.StreamSettings(device, device_index=None, sample_rate=sample_rate)
        indata = audio.AudioData.load_as_wav(in_path, settings)
        raw = indata.get_raw_data()

        labels = load_labels(labels_path)

        # ranges = [[labels[i-1][0], labels[i][0]] for i in range(1, len(labels))]
        # ranges.append([labels[-1][0], len(raw) // settings.sample_width])
        # labels = ranges

        write(raw, settings, labels, out_dir)


    except KeyboardInterrupt:
        print('KeyboardInterrupt')
    finally:
        device.terminate()
