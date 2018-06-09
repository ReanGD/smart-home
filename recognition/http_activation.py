import json
from threading import Thread, Event
from .base import HotwordRecognizer, HotwordRecognizerConfig
from .audio_settings import AudioSettings
from http.server import BaseHTTPRequestHandler, HTTPServer


class HttpHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        text = self.server.wait_answer()
        if text is None:
            self.send_response(204)
        else:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'command': text}).encode())


class HttpServer(Thread, HTTPServer):
    def __init__(self, port):
        server_address = ('', port)

        Thread.__init__(self)
        HTTPServer.__init__(self, server_address, HttpHandler)

        self._request_received = Event()
        self._answer = None
        self._answer_received = Event()
        self.start()

    def start_wait(self):
        self._request_received.clear()
        self._answer_received.clear()

    def is_request_received(self):
        result =  self._request_received.is_set()
        self._request_received.clear()
        return result

    def wait_answer(self):
        self._request_received.set()
        self._answer_received.wait()
        answer = self._answer
        self._answer = None
        return answer

    def set_answer(self, answer):
        self._answer = answer
        self._answer_received.set()

    def run(self):
        try:
            self.serve_forever()
        except KeyboardInterrupt:
            pass
        self.server_close()


class HttpActivation(HotwordRecognizer):
    def __init__(self, config):
        super().__init__(config)
        self._audio_settings = AudioSettings(channels=1)
        self._server = HttpServer(config.port)

    def set_answer(self, answer):
        self._server.set_answer(answer)

    def get_audio_settings(self) -> AudioSettings:
        return self._audio_settings

    def start(self):
        self._server.start_wait()

    def is_hotword(self, raw_frames) -> bool:
        return self._server.is_request_received()


class HttpActivationConfig(HotwordRecognizerConfig):
    def __init__(self, port):
        self.port = port

    def create_hotword_recognizer(self):
        return HttpActivation(self)
