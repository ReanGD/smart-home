import pytest
import asyncio
import logging
from test.test_proto import *
from protocols.home_assistant import HASerrializeProtocol
from protocols.transport import TCPClientConnection, TCPServerConnection, TCPServer


pytestmark = pytest.mark.asyncio


class ServerConnection(TCPServerConnection):
    def __init__(self, logger, event: asyncio.Event):
        super().__init__(logger)
        self.event = event
        self.recv_messages = []

    async def on_message1(self, message: Message1):
        self.recv_messages.append((message.DESCRIPTOR.name, message.text))
        await self.send(Message1Result(text=message.DESCRIPTOR.name + 'Response'))

    async def on_message1_result(self, message: Message1Result):
        self.recv_messages.append((message.DESCRIPTOR.name, message.text))
        await self.send(Message2(text=message.DESCRIPTOR.name + 'Request'))

    async def on_message2(self, message: Message2):
        self.recv_messages.append((message.DESCRIPTOR.name, message.text))
        await self.send(Message2Result(text=message.DESCRIPTOR.name + 'Response'))

    async def on_message2_result(self, message: Message2Result):
        self.recv_messages.append((message.DESCRIPTOR.name, message.text))
        self.event.set()


class ClientConnection(TCPClientConnection):
    def __init__(self, logger, event: asyncio.Event):
        super().__init__(logger)
        self.event = event
        self.recv_messages = []

    async def on_message1(self, message: Message1):
        self.recv_messages.append((message.DESCRIPTOR.name, message.text))
        await self.send(Message1Result(text=message.DESCRIPTOR.name + 'Response'))

    async def on_message1_result(self, message: Message1Result):
        self.recv_messages.append((message.DESCRIPTOR.name, message.text))
        await self.send(Message2(text=message.DESCRIPTOR.name + 'Request'))

    async def on_message2(self, message: Message2):
        self.recv_messages.append((message.DESCRIPTOR.name, message.text))
        await self.send(Message2Result(text=message.DESCRIPTOR.name + 'Response'))

    async def on_message2_result(self, message: Message2Result):
        self.recv_messages.append((message.DESCRIPTOR.name, message.text))
        self.event.set()


class TestTransport:
    def setup(self):
        self.host = '127.0.0.1'
        self.port = 8888
        self.finish_event = asyncio.Event()
        types = [Message1, Message1Result, Message2, Message2Result]

        self.server_protocol = HASerrializeProtocol(types, self.get_logger('server'))
        self.client_protocol = HASerrializeProtocol(types, self.get_logger('client'))

    def get_logger(self, logger_name):
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)

        return logger

    async def create_server(self):
        server = TCPServer(self.get_logger('server'))

        def handler_factory(logger):
            return ServerConnection(logger, self.finish_event)
        return await server.run(self.host, self.port, handler_factory, self.server_protocol)

    async def create_client(self):
        client = ClientConnection(self.get_logger('client'), self.finish_event)
        await client.connect(self.host, self.port, self.client_protocol)
        return client

    async def test_client_send(self):
        server = await self.create_server()
        client = await self.create_client()

        await client.send(Message1(text='Request'))

        await self.finish_event.wait()
        await client.close()
        await asyncio.sleep(0.1)
        await server.close()

    async def test_server_send(self):
        server = await self.create_server()
        client = await self.create_client()

        await server.send_to_all(Message1(text='Request'))

        await self.finish_event.wait()
        await client.close()
        await asyncio.sleep(0.1)
        await server.close()
