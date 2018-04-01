import collections
import voice_recognizer as vr


def check_one(device, is_mic, vad, settings: vr.StreamSettings, path, is_write):
    if is_mic:
        stream = device.create_microphone_stream(settings)
    else:
        raw_data = vr.AudioFile.read_wav(path, settings)
        stream = device.create_data_stream(raw_data, settings)

    # valid = 80, 160, 240
    frames_read = 160  # 10 ms
    # print("chank = {} ms".format(frames_read * 1000 / settings.sample_rate))
    vad.set_frames_read(frames_read)

    ring_buffer = collections.deque(maxlen=50)
    ring_voice_frames = collections.deque(maxlen=50)
    state_active = False
    ind = 0
    start_period = 0
    periods = []
    voice_frames = []
    while True:
        frames = stream.read(frames_read)
        if len(frames) != frames_read * settings.sample_width:
            break

        is_speech = vad.is_speech(frames)
        ring_buffer.append((ind, is_speech))
        ind += 1

        if is_write:
            ring_voice_frames.append(frames)

        if not state_active:
            num_voiced = len([1 for _, speech in ring_buffer if speech])
            if num_voiced > 0.9 * len(ring_buffer):
                start_period = ring_buffer[0][0]
                state_active = True
                voice_frames = list(ring_voice_frames)
        else:
            num_unvoiced = len([1 for _, speech in ring_buffer if not speech])
            if num_unvoiced > 0.9 * len(ring_buffer):
                state_active = False
                stop_period = ring_buffer[0][0]
                periods.append((start_period, stop_period))
                if is_write:
                    data = b''.join(voice_frames)
                    out_path = "samples_out/record{}.wav".format(len(periods))
                    vr.AudioData(data, settings).write_wav_data(out_path)
                    voice_frames.clear()
            elif is_write:
                voice_frames.append(frames)

    if state_active:
        stop_period = ind
        periods.append((start_period, stop_period))
        if is_write:
            data = b''.join(voice_frames)
            vr.AudioData(data, settings).write_wav_data(
                "samples_out/record{}.wav".format(len(periods)))
            voice_frames.clear()

    print("{}: {}".format(path, ", ".join(["{}:{}".format(start_period, stop_period - start_period)
                                           for start_period, stop_period in periods])))


def check_all(vad):
    is_mic = False
    is_write = False

    paths = ['samples/voice.wav', 'samples/voice_music_1.wav', 'samples/voice_music_2.wav',
             'samples/voice_music_3.wav', 'samples/voice_music_4.wav', 'samples/voice_music_5.wav',
             'samples/voice_music_6.wav', 'samples/voice_music_7.wav', 'samples/voice_music_8.wav',
             'samples/voice_noise_1.wav', 'samples/voice_noise_2.wav', 'samples/voice_noise_3.wav',
             'samples/voice_noise_4.wav', 'samples/voice_noise_5.wav', 'samples/voice_noise_6.wav',
             'samples/voice_noise_7.wav', 'samples/voice_noise_8.wav', ]

    if is_write:
        paths = ['samples/voice_music_6.wav']

    device = vr.Device()

    try:
        settings = vad.get_audio_settings(device)
        print("settings: {}".format(settings))

        for path in paths:
            vad = vad.clone()
            check_one(device, is_mic, vad, settings, path, is_write)
            device.close_streams()
    finally:
        device.terminate()
