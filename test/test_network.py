import unittest
import asyncio
from test.test_proto import *
from protocols.transport import ProtoConnection, create_server, create_client
from protocols.home_assistant import HASerrializeProtocol

import logging
from sys import stdout


class HandlerMain(object):
    def __init__(self):
        self.recv_messages = []

    async def on_connect(self):
        pass

    async def on_TestMessage1(self, conn: ProtoConnection, message: TestMessage1):
        self.recv_messages.append((message.DESCRIPTOR.name, message.text))
        await conn.send_protobuf(TestMessage1Result(text=message.DESCRIPTOR.name+'Response'))

    async def on_TestMessage1Result(self, conn: ProtoConnection, message: TestMessage1Result):
        self.recv_messages.append((message.DESCRIPTOR.name, message.text))
        await conn.send_protobuf(TestMessage2(text=message.DESCRIPTOR.name+'Request'))

    async def on_TestMessage2(self, conn: ProtoConnection, message: TestMessage2):
        self.recv_messages.append((message.DESCRIPTOR.name, message.text))
        await conn.send_protobuf(TestMessage2Result(text=message.DESCRIPTOR.name+'Response'))

    async def on_TestMessage2Result(self, conn: ProtoConnection, message: TestMessage2Result):
        self.recv_messages.append((message.DESCRIPTOR.name, message.text))
        pass


class TestNetwork(unittest.TestCase):
    def setUp(self):
        self.host = '127.0.0.1'
        self.port = 8888
        types = [TestMessage1, TestMessage1Result, TestMessage2, TestMessage2Result]

        self.log_handler = logging.StreamHandler(stdout)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
        self.log_handler.setFormatter(formatter)

        self.server_protocol = HASerrializeProtocol(types, self.get_logger('server'))
        self.client_protocol = HASerrializeProtocol(types, self.get_logger('client'))

    def tearDown(self):
        asyncio.get_event_loop().close()

    def get_logger(self, logger_name):
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(self.log_handler)

        return logger

    async def create_server(self, handler_factory):
        return await create_server(self.host, self.port, handler_factory, self.server_protocol,
                                   self.get_logger('server'))

    async def create_client(self, handler_factory):
        return await create_client(self.host, self.port, handler_factory, self.client_protocol,
                                   self.get_logger('client'))

    def test_client_server(self):
        async def client_server():
            server = await self.create_server(HandlerMain)
            client = await self.create_client(HandlerMain)

            await client.send_protobuf(TestMessage1(text='Request'))
            await asyncio.sleep(1)
            await client.close()
            await server.close()

        asyncio.get_event_loop().run_until_complete(client_server())
