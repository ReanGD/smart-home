import _portaudio as pa


PA_INT32: int = pa.paInt32
PA_INT24: int = pa.paInt24
PA_INT16: int = pa.paInt16
PA_UINT8: int = pa.paUInt8

PA_FORMATS = {PA_INT32: "PA_INT32",
              PA_INT24: "PA_INT24",
              PA_INT16: "PA_INT16",
              PA_UINT8: "PA_UINT8"}


def get_format_from_width(width: int) -> int:
    if width == 1:
        return PA_UINT8
    if width == 2:
        return PA_INT16
    if width == 3:
        return PA_INT24
    if width == 4:
        return PA_INT32

    raise ValueError("Invalid width: %d" % width)
