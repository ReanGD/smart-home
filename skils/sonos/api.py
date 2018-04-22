import soco
from .soap_client import MusicServiceSoapClient
from soco.music_services import MusicService, Account
from soco.data_structures import DidlObject, DidlResource


class DidlCustom(DidlObject):
    item_class = ''
    _translation = DidlObject._translation.copy()
    _translation.update(
        {
            'album_art_uri': ('upnp', 'albumArtURI'),
        }
    )


class SonosApi(object):
    def __init__(self, service_name, username, password):
        devices = list(soco.discover())
        assert len(devices) != 0, 'Not found sonos devices'
        self.device = devices[0]
        account = Account()
        ms = MusicService(service_name, account)
        ms.soap_client = MusicServiceSoapClient(ms.secure_uri, ms.soap_client.timeout,
                                                ms, username, password)
        self.music_service = ms

    @staticmethod
    def _get_didl(item, parent_id):
        restricted = False  # why?
        serial_num = 0  # why?
        desc = 'SA_RINCON{}_{}'.format(item.music_service.service_type, serial_num)

        if item.item_type == 'container':
            object_id = '100f006c' + item.id
            parent_id = '1008006c' + parent_id
            uri = 'x-rincon-cpcontainer:' + object_id
            protocol_info = 'x-rincon-cpcontainer:*:*:*'
            item_class = 'object.container.storageFolder'
        else:
            raise Exception('Unknown item_type = {}'.format(item.item_type))

        res = [DidlResource(uri=uri, protocol_info=protocol_info)]
        DidlCustom.item_class = item_class
        return DidlCustom(resources=res,
                          title=item.title,
                          album_art_uri=item.album_art_uri,
                          parent_id=parent_id,
                          item_id=object_id,
                          restricted=restricted,
                          desc=desc)

    def _get_didl_by_search(self, search_item):
        metadata = self.music_service.get_metadata(search_item, recursive=True)
        items = [item for item in metadata
                 if item.item_type == 'container' and 'can_play' in item.metadata]
        assert len(items) == 1, 'Len items can be 0'
        return SonosApi._get_didl(items[0], search_item.id)

    def search(self, category, term):
        for it in self.music_service.search(category=category, term=term, index=0, count=100):
            return self._get_didl_by_search(it)

        return None

    def play(self, didl):
        self.device.clear_queue()
        self.device.add_to_queue(didl, position=0, as_next=False)
        self.device.play()
