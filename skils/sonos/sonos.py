import soco
from xmltodict import parse
from soco.xml import XML
from soco.exceptions import MusicServiceException
from soco.music_services import MusicService, Account
from soco.soap import SoapFault, SoapMessage
from soco.data_structures import DidlObject, DidlResource


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
            top_track_m = self.music_service.get_metadata(top_track, recursive=True)
            # uri = self.music_service.get_media_uri(top_track.id)
            # self.device.add_uri_to_queue(uri)
            # self.device.add_to_queue(top_track)
            # top_track_m_1 = self.music_service.get_extended_metadata(top_track.item_id)
            # top_track_m = self.music_service.get_media_metadata(top_track.item_id)
            # media_metadata = self.music_service.get_media_uri(top_track.item_id)
            # print(media_metadata)
            # for itt in metadata:
            #     print(itt)
            # self.device.add_to_queue(metadata[1])
            for track in top_track_m:
                # self.music_service.sonos_uri_from_id(track.id)
                # self.device.add_to_queue(item, position, as_next)
                # http://cdnt-proxy-a.deezer.com/api/1/a08c68e3c372f615205b47493824d362dc49306a2d96453393129c3d1a3c3310f97aaece9e58a08dd9a69708680d98153a17c72b11fc046d7bda2ea075099d1ad731d88e21bb74b04cd3152bbd5baab5.mp3?hdnea=exp=1524358795~acl=/api/1/a08c68e3c372f615205b47493824d362dc49306a2d96453393129c3d1a3c3310f97aaece9e58a08dd9a69708680d98153a17c72b11fc046d7bda2ea075099d1ad731d88e21bb74b04cd3152bbd5baab5.mp3*~hmac=91eb314fc7e5ea131faed4e068d66edd81fdcaf063b2842e1e69e867d681b216&
                # 'soco://0ffffffftr%253A102529062?sid=2&sn='
                uri = self.music_service.get_media_uri(track.item_id)
                print(track.uri)
                print(uri)
                self.device.add_uri_to_queue(uri)
                self.device.add_uri_to_queue('soco://0ffffffftr%253A102529062?sid=2&sn=')
                # res = [DidlResource(uri=uri, protocol_info="x-rincon-playlist:*:*:*")]
                # item = DidlObject(resources=res, title='', parent_id='', item_id='')
                # position = 0
                # as_next = False
                # self.device.add_to_queue(item, position, as_next)
