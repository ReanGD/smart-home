import _portaudio as pa


paFloat32 = pa.paFloat32
paInt32 = pa.paInt32
paInt24 = pa.paInt24
paInt16 = pa.paInt16
paInt8 = pa.paInt8
paUInt8 = pa.paUInt8

paFormats = {paFloat32: "paFloat32",
             paInt32: "paInt32",
             paInt24: "paInt24",
             paInt16: "paInt16",
             paInt8: "paInt8",
             paUInt8: "paUInt8"}


def get_format_from_width(width, unsigned=True):
    if width == 1:
        if unsigned:
            return paUInt8
        else:
            return paInt8
    elif width == 2:
        return paInt16
    elif width == 3:
        return paInt24
    elif width == 4:
        return paFloat32
    else:
        raise ValueError("Invalid width: %d" % width)
