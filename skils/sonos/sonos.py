import soco
from xmltodict import parse
from soco.xml import XML
from soco.exceptions import MusicServiceException
from soco.music_services import MusicService, Account
from soco.soap import SoapFault, SoapMessage
from soco.data_structures import DidlObject, DidlResource, to_didl_string


class MusicServiceSoapClient(object):
    def __init__(self, endpoint, timeout, music_service, username, password):
        self.endpoint = endpoint
        self.timeout = timeout
        self.music_service = music_service
        self._cached_soap_header = None
        self._session_id = None
        self._session_id = self.call('getSessionId', [('username', username),
                                                      ('password', password)])['getSessionIdResult']

    def get_soap_header(self):
        if self._session_id is None:
            return ''

        if self._cached_soap_header is not None:
            return self._cached_soap_header

        credentials_header = XML.Element("credentials",
                                         {'xmlns': "http://www.sonos.com/Services/1.1"})

        if self.music_service.auth_type in ['UserId']:
            session_elt = XML.Element('sessionId')
            session_elt.text = self._session_id
            credentials_header.append(session_elt)
        else:
            raise Exception('unknown auth_type = ' + self.music_service.auth_type)

        self._cached_soap_header = XML.tostring(
            credentials_header,
            encoding='utf-8').decode(encoding='utf-8')
        return self._cached_soap_header

    def call(self, method, args=None):
        http_headers = {
            'Accept-Encoding': 'gzip, deflate',
            'User-Agent': 'Linux UPnP/1.0 Sonos/26.99-12345'
        }

        message = SoapMessage(
            endpoint=self.endpoint,
            method=method,
            parameters=[] if args is None else args,
            http_headers=http_headers,
            soap_action="http://www.sonos.com/Services/1"
                        ".1#{0}".format(method),
            soap_header=self.get_soap_header(),
            namespace='http://www.sonos.com/Services/1.1',
            timeout=self.timeout)

        try:
            result_elt = message.call()
        except SoapFault as exc:
            raise MusicServiceException(exc.faultstring, exc.faultcode)

        result = list(parse(
            XML.tostring(result_elt), process_namespaces=True,
            namespaces={'http://www.sonos.com/Services/1.1': None}
        ).values())[0]

        return result if result is not None else {}


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
        print(text)
        albums = self.device.music_library.get_albums(search_term='Black')
        for album in albums:
            print('Added:', album.title)

        self.device.clear_queue()
        for it in self.music_service.search(category='artists', term='Наутилус'):
            # it -> MSArtist
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

