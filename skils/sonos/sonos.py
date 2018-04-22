from .api import SonosApi


class SonosSkill(object):
    def __init__(self, service_name, username, password):
        self._api = SonosApi(service_name, username, password)

    def run(self, text):
        didl = self._api.search('artists', text)
        if didl is None:
            return False

        self._api.play(didl)
        return True
