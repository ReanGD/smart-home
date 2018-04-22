import soco
from .soap_client import MusicServiceSoapClient
from soco.music_services import MusicService, Account
from soco.data_structures import DidlObject, DidlResource, to_didl_string


class DidlContainerFolder(DidlObject):
    item_class = 'object.container.storageFolder'
    tag = 'container'


class SonosSkill(object):
    def __init__(self, service_name, username, password):
        devices = list(soco.discover())
        assert len(devices) != 0, 'Not found sonos devices'
        self.device = devices[0]
        account = Account()
        ms = MusicService(service_name, account)
        ms.soap_client = MusicServiceSoapClient(ms.secure_uri, ms.soap_client.timeout,
                                                ms, username, password)
        self.music_service = ms

    def run(self, text):
        self.device.clear_queue()
        for it in self.music_service.search(category='artists', term=text):
            metadata = self.music_service.get_metadata(it)
            top_track = metadata[1]

            uri = "x-rincon-cpcontainer:100f006c" + top_track.id
            position = 0
            as_next = True

            parent_id = '1008006c' + it.id
            item_id = '100f006c' + top_track.id
            restricted = False
            protocol_info = "x-rincon-cpcontainer:*:*:*"
            title = top_track.title
            res = [DidlResource(uri=uri, protocol_info=protocol_info)]
            item = DidlContainerFolder(resources=res, title=title, parent_id=parent_id, item_id=item_id, restricted=restricted, desc='SA_RINCON519_0')
            print(to_didl_string(item))

            self.device.add_to_queue(item, position, as_next)
            self.device.play()

