import asyncio

from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, create_autospec, sentinel as s

from routerosc.connection import Connection
from routerosc.dispatcher import Dispatcher


class DispatcherTest(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        async def connection_read():
            x = await self.connection_queue.get()
            if isinstance(x, BaseException):
                raise x
            return x
        self.connection_queue = asyncio.Queue()
        self.connection = create_autospec(Connection, instance=True)
        self.connection.read.side_effect = connection_read
        self.queue_size = 2
        self.tags = MagicMock()
        self.dispatcher = Dispatcher(
            self.connection,
            queue_size=self.queue_size,
            tags=self.tags)

    def feed(self, x):
        self.connection_queue.put_nowait(x)


class DispatcherCloseTest(DispatcherTest):
    async def test(self):
        await self.dispatcher.close()
        self.connection.close.assert_awaited_once()

    async def test_connection_error(self):
        self.connection.close.side_effect = ConnectionError
        with self.assertRaises(ConnectionError):
            await self.dispatcher.close()


class DispatcherReadTest(DispatcherTest):
    async def asyncSetUp(self):
        await super().asyncSetUp()
        self.tag = await self.dispatcher.send(s.command)
        self.reader = asyncio.create_task(self.dispatcher.read(self.tag))

    async def assert_started(self):
        await asyncio.sleep(0)
        self.assertEqual(self.connection.read.await_count, 1)

    async def assert_reading(self):
        await asyncio.sleep(0)
        self.assertEqual(self.connection.read.await_count, 2)

    async def assert_stopped(self, result):
        for reader in self.reader, self.dispatcher.read(self.tag):
            if isinstance(result, tuple):
                self.assertEqual(await reader, result)
            else:
                with self.assertRaises(result):
                    await reader
        self.feed(s.reply)
        await asyncio.sleep(0)
        self.assertEqual(self.connection.read.await_count, 1)

    async def test(self):
        await self.assert_started()

    async def test_reply(self):
        self.feed((s.kind, s.data, {'tag': self.tag}))
        self.assertEqual(await self.reader, (s.kind, s.data))
        await self.assert_reading()

    async def test_reply_with_unexpected_tag(self):
        self.feed((s.kind, s.data, {'tag': s.unexpected_tag}))
        await self.assert_reading()

    async def test_unexpected_reply(self):
        self.feed(s.unexpected_reply)
        await self.assert_stopped(RuntimeError)

    async def test_fatal_reply(self):
        self.feed((b'!fatal', s.reason))
        await self.assert_stopped((b'!fatal', s.reason))

    async def test_no_reply(self):
        self.feed(ConnectionError())
        await self.assert_stopped(ConnectionError)

    async def test_close(self):
        await self.dispatcher.close()
        await self.assert_stopped(RuntimeError)


class DispatcherSendTest(DispatcherTest):
    async def test(self):
        self.tags.__next__.return_value = s.tag
        self.assertEqual(await self.dispatcher.send(
            s.command, s.attributes, query=s.query), s.tag)
        self.connection.send.assert_awaited_once_with(
            s.command, s.attributes, query=s.query, api={'tag': s.tag})

    async def test_bad_command(self):
        self.connection.send.side_effect = ValueError
        with self.assertRaises(ValueError):
            await self.dispatcher.send(s.command)

    async def test_connection_error(self):
        self.connection.send.side_effect = ConnectionError
        with self.assertRaises(ConnectionError):
            await self.dispatcher.send(s.command)


class DispatcherDropTest(DispatcherTest):
    async def test(self):
        tag = await self.dispatcher.send(s.command)
        self.dispatcher.drop(tag)
        with self.assertRaises(KeyError):
            self.dispatcher.drop(tag)
        with self.assertRaises(KeyError):
            await self.dispatcher.read(tag)


class DispatcherBackpressureTest(DispatcherTest):
    async def test(self):
        tag = await self.dispatcher.send(s.command)
        for _ in range(self.queue_size + 2):
            self.feed((s.kind, s.data, {'tag': tag}))
        await asyncio.sleep(0)
        self.assertEqual(self.connection.read.await_count, self.queue_size + 1)
        await self.dispatcher.read(tag)
        await asyncio.sleep(0)
        self.assertEqual(self.connection.read.await_count, self.queue_size + 2)
        self.dispatcher.drop(tag)
        await asyncio.sleep(0)
        self.assertEqual(self.connection.read.await_count, self.queue_size + 3)
