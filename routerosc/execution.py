from . import errors


async def create(dispatcher, command, attributes={}, query=None):
    return Execution(dispatcher, command, attributes, query,
                     await dispatcher.send(command, attributes, query))


class Execution:
    def __init__(self, dispatcher, command, attributes, query, tag):
        self.dispatcher = dispatcher
        self.command = command
        self.attributes = attributes
        self.query = query
        self.tag = tag

        self.errors = []
        self.result = None
        self.reader = self.read()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        await self.close()

    def __aiter__(self):
        return self

    async def __anext__(self):
        return await self.reader.__anext__()

    async def read(self):
        while self.result is None:
            match await self.dispatcher.read(self.tag):
                case [b'!done', result]:
                    self.result = result
                case [b'!empty', {}]:
                    continue
                case [b'!re', data]:
                    yield data
                case [b'!trap', error]:
                    self.errors.append(error)
                case [b'!fatal', reason]:
                    raise errors.ServiceError(reason)
                case reply:
                    raise RuntimeError(f"Unexpected reply: {reply}")
        if self.errors:
            raise errors.CommandError(self)

    async def close(self):
        await self.reader.aclose()
        self.dispatcher.drop(self.tag)
        if self.result is None and self.command != '/cancel':
            execution = await create(self.dispatcher, '/cancel', {'tag': self.tag})
            async with execution:
                async for _ in execution:
                    continue
