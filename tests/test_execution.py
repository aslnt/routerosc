import asyncio

from unittest import IsolatedAsyncioTestCase
from unittest.mock import create_autospec, sentinel as s

from routerosc.dispatcher import Dispatcher
from routerosc.errors import CommandError, ServiceError
from routerosc.execution import Execution


class ExecutionTest(IsolatedAsyncioTestCase):
    def setUp(self):
        self.dispatcher = create_autospec(Dispatcher, instance=True)
        self.execution = Execution(self.dispatcher, s.command, s.attributes, s.query, s.tag)


class ExecutionCloseTest(ExecutionTest):
    def setUp(self):
        super().setUp()
        self.dispatcher.send.return_value = s.cancel_tag
        self.dispatcher.read.return_value = b'!done', s.cancel_result

    async def assert_dropped(self):
        with self.assertRaises(StopAsyncIteration):
            await anext(self.execution)
        self.dispatcher.drop.assert_any_call(s.tag)

    async def assert_closed(self):
        await self.assert_dropped()
        self.dispatcher.send.assert_awaited_once_with('/cancel', {'tag': s.tag}, None)
        self.dispatcher.read.assert_awaited_once_with(s.cancel_tag)
        self.dispatcher.drop.assert_called_with(s.cancel_tag)

    async def test(self):
        await self.execution.close()
        await self.assert_closed()

    async def test_connection_error_during_read(self):
        self.dispatcher.read.side_effect = ConnectionError
        with self.assertRaises(ConnectionError):
            await self.execution.close()
        await self.assert_closed()

    async def test_connection_error_during_send(self):
        self.dispatcher.send.side_effect = ConnectionError
        with self.assertRaises(ConnectionError):
            await self.execution.close()
        await self.assert_dropped()


class ExecutionReadTest(ExecutionTest):
    async def test(self):
        await asyncio.gather(anext(self.execution), return_exceptions=True)
        self.dispatcher.read.assert_awaited_once_with(s.tag)

    async def test_done_reply(self):
        self.dispatcher.read.side_effect = [(b'!done', s.result)]
        with self.assertRaises(StopAsyncIteration):
            await anext(self.execution)
        self.assertEqual(self.execution.result, s.result)

    async def test_empty_reply(self):
        self.dispatcher.read.side_effect = [(b'!empty', {}), (b'!done', s.result)]
        with self.assertRaises(StopAsyncIteration):
            await anext(self.execution)

    async def test_re_reply(self):
        self.dispatcher.read.side_effect = [(b'!re', s.data_0), (b'!re', s.data_1)]
        self.assertEqual(await anext(self.execution), s.data_0)
        self.assertEqual(await anext(self.execution), s.data_1)

    async def test_trap_reply(self):
        self.dispatcher.read.side_effect = [
            (b'!trap', s.error_0), (b'!trap', s.error_1), (b'!done', s.result),
        ]
        with self.assertRaises(CommandError) as x:
            await anext(self.execution)
        self.assertEqual(x.exception.execution.errors, [s.error_0, s.error_1])

    async def test_fatal_reply(self):
        self.dispatcher.read.side_effect = [(b'!fatal', s.reason)]
        with self.assertRaises(ServiceError) as x:
            await anext(self.execution)
        self.assertEqual(x.exception.reason, s.reason)

    async def test_unexpected_reply(self):
        self.dispatcher.read.side_effect = [None]
        with self.assertRaises(RuntimeError):
            await anext(self.execution)

    async def test_unexpected_error(self):
        self.dispatcher.read.side_effect = RuntimeError
        with self.assertRaises(RuntimeError):
            await anext(self.execution)

    async def test_connection_error(self):
        self.dispatcher.read.side_effect = ConnectionError
        with self.assertRaises(ConnectionError):
            await anext(self.execution)
