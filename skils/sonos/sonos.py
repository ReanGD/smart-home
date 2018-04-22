from .client import Client


class Sonos(object):
    def __init__(self, settings):
        self._client = Client(settings.service_name, settings.username, settings.password)

    def run(self, text):
        didl = self._client.search('artists', text)
        if didl is None:
            return False

        self._client.play(didl)
        return True


class SonosConfig(object):
    def __init__(self, service_name, username, password):
        self.service_name = service_name
        self.username = username
        self.password = password

    def create_skill(self):
        return Sonos(self)
