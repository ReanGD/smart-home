from xmltodict import parse
from soco.xml import XML
from soco.soap import SoapFault, SoapMessage
from soco.exceptions import MusicServiceException


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