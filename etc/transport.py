from protocols.transport import TransportConfig


class HassTransportConfig(TransportConfig):
    def __init__(self):
        super().__init__('192.168.1.3', 8083)


class YanexTransportConfig(TransportConfig):
    def __init__(self):
        super().__init__('asr.yandex.net', 443)
