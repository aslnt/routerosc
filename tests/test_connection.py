import asyncio

from unittest import IsolatedAsyncioTestCase
from unittest.mock import create_autospec, patch, sentinel as s

from routerosc.connection import Connection


class ConnectionTest(IsolatedAsyncioTestCase):
    def setUp(self):
        self.reader = s.reader
        self.writer = create_autospec(asyncio.StreamWriter, instance=True)
        self.connection = Connection(self.reader, self.writer)


class ConnectionCloseTest(ConnectionTest):
    async def test(self):
        await self.connection.close()
        self.writer.close.assert_called_once()
        self.writer.wait_closed.assert_awaited_once()

    async def test_connection_error(self):
        self.writer.wait_closed.side_effect = ConnectionError
        with self.assertRaises(ConnectionError):
            await self.connection.close()


@patch('routerosc.connection.send_sentence', autospec=True)
@patch('routerosc.connection.dump_command', autospec=True)
class ConnectionSendTest(ConnectionTest):
    async def test(self, dump_command, send_sentence):
        dump_command.return_value = s.sentence
        await self.connection.send(s.name, s.attributes, s.query, s.api)
        dump_command.assert_called_once_with(s.name, s.attributes, s.query, s.api)
        send_sentence.assert_awaited_once_with(self.writer, s.sentence)

    async def test_bad_command(self, dump_command, _):
        dump_command.side_effect = ValueError
        with self.assertRaises(ValueError):
            await self.connection.send(s.name, s.attributes, s.query, s.api)

    async def test_bad_sentence(self, _, send_sentence):
        send_sentence.side_effect = ValueError
        with self.assertRaises(ValueError):
            await self.connection.send(s.name, s.attributes, s.query, s.api)

    async def test_connection_error(self, _, send_sentence):
        send_sentence.side_effect = ConnectionError
        with self.assertRaises(ConnectionError):
            await self.connection.send(s.name, s.attributes, s.query, s.api)


@patch('routerosc.connection.parse_reply', autospec=True)
@patch('routerosc.connection.read_sentence', autospec=True)
class ConnectionReadTest(ConnectionTest):
    async def test(self, read_sentence, parse_reply):
        read_sentence.return_value = s.sentence
        parse_reply.return_value = s.reply
        self.assertEqual(await self.connection.read(), s.reply)
        parse_reply.assert_called_once_with(s.sentence)
        read_sentence.assert_awaited_once_with(self.reader)

    async def test_bad_reply(self, _, parse_reply):
        parse_reply.side_effect = ValueError
        with self.assertRaises(RuntimeError):
            await self.connection.read()

    async def test_bad_sentence(self, read_sentence, _):
        read_sentence.side_effect = RuntimeError
        with self.assertRaises(RuntimeError):
            await self.connection.read()

    async def test_incomplete_sentence(self, read_sentence, _):
        read_sentence.side_effect = asyncio.IncompleteReadError(b'', 1)
        with self.assertRaises(ConnectionError):
            await self.connection.read()
