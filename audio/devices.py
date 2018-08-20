import _portaudio as pa


class DeviceInfo:
    def __init__(self, default: bool, index: int, name: str, max_input_channels: int,
                 default_sample_rate: float):
        # pylint: disable=too-many-arguments
        self._default = default
        self._index = index
        self._name = name
        self._max_input_channels = max_input_channels
        self._default_sample_rate = default_sample_rate

    @property
    def default(self) -> bool:
        return self._default

    @property
    def index(self) -> int:
        return self._index

    @property
    def name(self) -> str:
        return self._name

    @property
    def max_input_channels(self) -> int:
        return self._max_input_channels

    @property
    def default_sample_rate(self) -> float:
        return self._default_sample_rate

    def __str__(self) -> str:
        msg = '{}: "{}", maxInputChannels: {}, defaultSampleRate: {}'
        name = '(default) ' + self.name if self.default else self.name
        return msg.format(self.index, name, self.max_input_channels, self.default_sample_rate)


class Devices:
    @staticmethod
    def get_device_count() -> int:
        return pa.get_device_count()

    @staticmethod
    def get_real_index(device_index: [int, None]) -> int:
        if device_index is not None:
            assert isinstance(device_index, int), "Device index must be None or an integer"
            count = Devices.get_device_count()
            msg = ("Device index out of range ({} devices available; "
                   "device index should be between 0 and {} inclusive)")
            assert 0 <= device_index < count, msg.format(count, count - 1)
            return device_index

        return pa.get_default_input_device()

    @staticmethod
    def get_device_info_by_index(device_index: int) -> DeviceInfo:
        default_index = Devices.get_real_index(device_index)
        device_info = pa.get_device_info(device_index)

        try:
            device_name = device_info.name.decode('utf-8')
        except UnicodeDecodeError:
            device_name = device_info.name.decode('cp1252')
        default = default_index == device_index

        return DeviceInfo(default, default_index, device_name,
                          device_info.maxInputChannels, device_info.defaultSampleRate)
