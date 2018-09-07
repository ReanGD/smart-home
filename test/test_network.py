import unittest
import asyncio
from test.test_proto import *
from protocols.home_assistant import HASerrializeProtocol
from protocols.transport import TCPClientConnection, TCPServerConnection, TCPServer

import logging
from sys import stdout


log_handler = logging.StreamHandler(stdout)
log_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s'))


class TestServerConnection(TCPServerConnection):
    def __init__(self, logger, event: asyncio.Event):
        super().__init__(logger)
        self.event = event
        self.recv_messages = []

    async def on_test_message1(self, message: TestMessage1):
        self.recv_messages.append((message.DESCRIPTOR.name, message.text))
        await self.send(TestMessage1Result(text=message.DESCRIPTOR.name + 'Response'))

    async def on_test_message1_result(self, message: TestMessage1Result):
        self.recv_messages.append((message.DESCRIPTOR.name, message.text))
        await self.send(TestMessage2(text=message.DESCRIPTOR.name + 'Request'))

    async def on_test_message2(self, message: TestMessage2):
        self.recv_messages.append((message.DESCRIPTOR.name, message.text))
        await self.send(TestMessage2Result(text=message.DESCRIPTOR.name + 'Response'))

    async def on_test_message2_result(self, message: TestMessage2Result):
        self.recv_messages.append((message.DESCRIPTOR.name, message.text))
        self.event.set()


class TestClientConnection(TCPClientConnection):
    def __init__(self, logger, event: asyncio.Event):
        super().__init__(logger)
        self.event = event
        self.recv_messages = []

    async def on_test_message1(self, message: TestMessage1):
        self.recv_messages.append((message.DESCRIPTOR.name, message.text))
        await self.send(TestMessage1Result(text=message.DESCRIPTOR.name + 'Response'))

    async def on_test_message1_result(self, message: TestMessage1Result):
        self.recv_messages.append((message.DESCRIPTOR.name, message.text))
        await self.send(TestMessage2(text=message.DESCRIPTOR.name + 'Request'))

    async def on_test_message2(self, message: TestMessage2):
        self.recv_messages.append((message.DESCRIPTOR.name, message.text))
        await self.send(TestMessage2Result(text=message.DESCRIPTOR.name + 'Response'))

    async def on_test_message2_result(self, message: TestMessage2Result):
        self.recv_messages.append((message.DESCRIPTOR.name, message.text))
        self.event.set()


class TestNetwork(unittest.TestCase):
    def setUp(self):
        self.host = '127.0.0.1'
        self.port = 8888
        self.finish_event = asyncio.Event()
        types = [TestMessage1, TestMessage1Result, TestMessage2, TestMessage2Result]

        self.server_protocol = HASerrializeProtocol(types, self.get_logger('server'))
        self.client_protocol = HASerrializeProtocol(types, self.get_logger('client'))

    def get_logger(self, logger_name):
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(log_handler)

        return logger

    async def create_server(self):
        server = TCPServer(self.get_logger('server'))

        def handler_factory(logger):
            return TestServerConnection(logger, self.finish_event)
        return await server.run(self.host, self.port, handler_factory, self.server_protocol)

    async def create_client(self):
        client = TestClientConnection(self.get_logger('client'), self.finish_event)
        await client.connect(self.host, self.port, self.client_protocol)
        return client

    def test_client_send(self):
        async def client_server():
            server = await self.create_server()
            client = await self.create_client()

            await client.send(TestMessage1(text='Request'))

            await self.finish_event.wait()
            await client.close()
            await asyncio.sleep(0.1)
            await server.close()

        asyncio.get_event_loop().run_until_complete(client_server())

    def test_server_send(self):
        async def client_server():
            server = await self.create_server()
            client = await self.create_client()

            await server.send_to_all(TestMessage1(text='Request'))

            await self.finish_event.wait()
            await client.close()
            await asyncio.sleep(0.1)
            await server.close()

        asyncio.get_event_loop().run_until_complete(client_server())
