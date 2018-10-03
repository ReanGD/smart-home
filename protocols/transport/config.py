class TransportConfig:
    def __init__(self, host: str, port: int):
        self._host = host
        self._port = port

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    @property
    def address(self) -> str:
        return '{}:{}'.format(self._host, self._port)

    def __str__(self) -> str:
        return self.address
