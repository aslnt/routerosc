import asyncio

from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import create_autospec, patch

from routerosc.sentence import encode_length, read_length, read_sentence, send_sentence

LENGTHS = {
    b'\x00': 0x00,
    b'\x7f': 0x7f,
    b'\x80\x80': 0x0080,
    b'\xbf\xff': 0x3fff,
    b'\xc0\x40\x00': 0x004000,
    b'\xdf\xff\xff': 0x1fffff,
    b'\xe0\x20\x00\x00': 0x0200000,
    b'\xef\xff\xff\xff': 0xfffffff,
    b'\xf0\x10\x00\x00\x00': 0x10000000,
    b'\xf0\xff\xff\xff\xff': 0xffffffff,
}

BAD_LENGTHS = [0x00, 0x100000000]

BAD_ENCODED_LENGTHS = [b'\xf1', b'\xff']


class EncodeLengthTest(TestCase):
    def test(self):
        for encoded, length in LENGTHS.items():
            if length:
                with self.subTest(length=hex(length)):
                    self.assertEqual(encode_length(length), encoded)

    def test_bad_length(self):
        for length in BAD_LENGTHS:
            with self.subTest(length=hex(length)):
                with self.assertRaises(ValueError):
                    encode_length(length)


class ReadLengthTest(IsolatedAsyncioTestCase):
    def setUp(self):
        self.reader = asyncio.StreamReader()

    async def test(self):
        for encoded, length in LENGTHS.items():
            with self.subTest(encoded=encoded):
                self.reader.feed_data(encoded)
                self.assertEqual(await read_length(self.reader), length)

    async def test_bad_length(self):
        for encoded in BAD_ENCODED_LENGTHS:
            with self.subTest(encoded=encoded):
                self.reader.feed_data(encoded)
                with self.assertRaises(RuntimeError):
                    await read_length(self.reader)


class SendSentenceTest(IsolatedAsyncioTestCase):
    def setUp(self):
        self.writer = create_autospec(asyncio.StreamWriter, instance=True)

    async def test(self):
        await send_sentence(self.writer, [b'a', b'bc'])
        self.writer.write.assert_called_once_with(b'\x01a\x02bc\x00')
        self.writer.drain.assert_awaited_once()

    @patch('routerosc.sentence.encode_length', autospec=True)
    async def test_bad_length(self, encode_length):
        encode_length.side_effect = ValueError
        with self.assertRaises(ValueError):
            await send_sentence(self.writer, [b'a', b'bc'])

    async def test_connection_error(self):
        self.writer.drain.side_effect = ConnectionError
        with self.assertRaises(ConnectionError):
            await send_sentence(self.writer, [b'a', b'bc'])


class ReadSentenceTest(IsolatedAsyncioTestCase):
    def setUp(self):
        self.reader = asyncio.StreamReader()

    async def test(self):
        self.reader.feed_data(b'\x01a\x02bc\x00')
        self.assertEqual(await read_sentence(self.reader), [b'a', b'bc'])

    async def test_incomplete_length(self):
        self.reader.feed_eof()
        with self.assertRaises(asyncio.IncompleteReadError):
            await read_sentence(self.reader)

    async def test_incomplete_word(self):
        self.reader.feed_data(b'\x01')
        self.reader.feed_eof()
        with self.assertRaises(asyncio.IncompleteReadError):
            await read_sentence(self.reader)

    @patch('routerosc.sentence.read_length', autospec=True)
    async def test_bad_length(self, read_length):
        read_length.side_effect = RuntimeError
        with self.assertRaises(RuntimeError):
            await read_sentence(self.reader)
