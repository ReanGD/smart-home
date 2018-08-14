import unittest
import asyncio
from test.test_proto import *
from protocols.transport import ProtoConnection, create_server, create_client
from protocols.home_assistant import HASerrializeProtocol

import logging
from sys import stdout


log_handler = logging.StreamHandler(stdout)
log_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s'))


class HandlerMain(object):
    def __init__(self, event: asyncio.Event):
        self.event = event
        self.recv_messages = []

    async def on_connect(self, conn: ProtoConnection):
        pass

    async def on_test_message1(self, conn: ProtoConnection, message: TestMessage1):
        self.recv_messages.append((message.DESCRIPTOR.name, message.text))
        await conn.send_protobuf(TestMessage1Result(text=message.DESCRIPTOR.name+'Response'))

    async def on_test_message1_result(self, conn: ProtoConnection, message: TestMessage1Result):
        self.recv_messages.append((message.DESCRIPTOR.name, message.text))
        await conn.send_protobuf(TestMessage2(text=message.DESCRIPTOR.name+'Request'))

    async def on_test_message2(self, conn: ProtoConnection, message: TestMessage2):
        self.recv_messages.append((message.DESCRIPTOR.name, message.text))
        await conn.send_protobuf(TestMessage2Result(text=message.DESCRIPTOR.name+'Response'))

    async def on_test_message2_result(self, conn: ProtoConnection, message: TestMessage2Result):
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

    async def create_server(self, handler_factory):
        return await create_server(self.host, self.port, handler_factory, self.server_protocol,
                                   self.get_logger('server'))

    async def create_client(self, handler_factory):
        return await create_client(self.host, self.port, handler_factory, self.client_protocol,
                                   self.get_logger('client'))

    def handler_generator(self):
        return HandlerMain(self.finish_event)

    def test_client_send(self):
        async def client_server():
            server = await self.create_server(self.handler_generator)
            client = await self.create_client(self.handler_generator)

            await client.send_protobuf(TestMessage1(text='Request'))

            await self.finish_event.wait()
            await client.close()
            await asyncio.sleep(0.1)
            await server.close()

        asyncio.get_event_loop().run_until_complete(client_server())

    def test_server_send(self):
        async def client_server():
            server = await self.create_server(self.handler_generator)
            client = await self.create_client(self.handler_generator)

            await server.send_protobuf_to_all(TestMessage1(text='Request'))

            await self.finish_event.wait()
            await client.close()
            await asyncio.sleep(0.1)
            await server.close()

        asyncio.get_event_loop().run_until_complete(client_server())
