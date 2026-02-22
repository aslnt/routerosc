import asyncio
import itertools

from .connection import create as create_connection


async def create(*args, queue_size=10, **kwargs):
    connection = await create_connection(*args, **kwargs)
    tags = generate_tags()
    return Dispatcher(connection, queue_size, tags)


def generate_tags():
    return (str(number).encode() for number in itertools.count())


class Dispatcher:
    def __init__(self, connection, queue_size, tags):
        self.connection = connection
        self.queue_size = queue_size
        self.tags = tags

        self.queues = {}
        self.worker = asyncio.create_task(self.run())

    async def close(self):
        self.worker.cancel()
        await asyncio.gather(self.worker, return_exceptions=True)
        await self.connection.close()

    async def send(self, *args, **kwargs):
        tag = next(self.tags)
        self.queues[tag] = asyncio.Queue(self.queue_size)
        try:
            await self.connection.send(*args, **kwargs, api={'tag': tag})
        except:
            self.drop(tag)
            raise
        return tag

    async def read(self, tag):
        getter = asyncio.create_task(self.queues[tag].get())
        try:
            await asyncio.wait((getter, self.worker), return_when=asyncio.FIRST_COMPLETED)
            if getter.done():
                return getter.result()
            try:
                return self.worker.result()
            except ConnectionError as e:
                raise ConnectionError(e) from e
            except BaseException as e:
                raise RuntimeError(e) from e
        finally:
            getter.cancel()
            await asyncio.gather(getter, return_exceptions=True)

    def drop(self, tag):
        if self.queues[tag].full():
            self.queues[tag].get_nowait()
        del self.queues[tag]

    async def run(self):
        while True:
            match await self.connection.read():
                case [b'!fatal', reason] as reply:
                    return reply
                case [kind, data, {'tag': tag}]:
                    try:
                        await self.queues[tag].put((kind, data))
                    except KeyError:
                        continue
                case reply:
                    raise RuntimeError(f"Unexpected reply: {reply!r}")
