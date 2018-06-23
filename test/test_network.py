import unittest
import asyncio
from test.test_proto import TestMessage, TestMessageResult
from protocols.transport import ProtoConnection, create_server, create_client
from protocols.home_assistant import HASerrializeProtocol

import logging
from sys import stdout


class HandlerServer(object):
    async def on_TestMessage(self, conn: ProtoConnection, message: TestMessage):
        await conn.send_protobuf(TestMessageResult(text = message.text + 'Result'))

    async def on_TestMessageResult(self, conn: ProtoConnection, message: TestMessageResult):
        pass


class HandlerClient(object):
    async def on_connect(self):
        pass

    async def on_TestMessage(self, conn: ProtoConnection, message: TestMessage):
        await conn.send_protobuf(TestMessageResult(text=message.text + 'Result'))

    async def on_TestMessageResult(self, conn: ProtoConnection, message: TestMessageResult):
        await conn.send_protobuf(TestMessageResult(text=message.text + 'Result'))


class TestNetwork(unittest.TestCase):
    def setUp(self):
        self.host = '127.0.0.1'
        self.port = 8888
        types = [TestMessage, TestMessageResult]
        self.server_logger = TestNetwork.get_logger('server')
        self.server_protocol = HASerrializeProtocol(types, self.server_logger)
        self.client_logger = TestNetwork.get_logger('client')
        self.client_protocol = HASerrializeProtocol(types, self.client_logger)

    @staticmethod
    def get_logger(logger_name):
        handler = logging.StreamHandler(stdout)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
        handler.setFormatter(formatter)

        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        return logger

    async def create_server(self, handler_class):
        return await create_server(self.host, self.port, handler_class, self.server_protocol,
                                   self.server_logger)

    async def create_client(self, handler_class):
        return await create_client(self.host, self.port, handler_class, self.client_protocol,
                                   self.client_logger)

    async def client_server(self):
        server = await self.create_server(HandlerServer)
        client = await self.create_client(HandlerClient)

        await client.send_protobuf(TestMessage(text='Hello'))
        await asyncio.sleep(1)

    def test_client_server(self):
        asyncio.get_event_loop().run_until_complete(self.client_server())
