import asyncio

from .command import dump_command
from .reply import parse_reply
from .sentence import read_sentence, send_sentence


async def create(host, port=8728):
    return Connection(*await asyncio.open_connection(host, port))


class Connection:
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer

    async def close(self):
        self.writer.close()
        await self.writer.wait_closed()

    async def send(self, *args, **kwargs):
        sentence = dump_command(*args, **kwargs)
        await send_sentence(self.writer, sentence)

    async def read(self):
        try:
            sentence = await read_sentence(self.reader)
        except asyncio.IncompleteReadError as e:
            raise ConnectionError(e) from e
        try:
            return parse_reply(sentence)
        except ValueError as e:
            raise RuntimeError(f"Bad reply: {sentence!r}") from e
