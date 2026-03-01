from .dispatcher import create as create_dispatcher
from .execution import create as create_execution
from .promise import promisify

create_execution = promisify(create_execution)


@promisify
async def create(*args, **kwargs):
    return Client(await create_dispatcher(*args, **kwargs))


class Client:
    def __init__(self, dispatcher):
        self.dispatcher = dispatcher

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        await self.close()

    def __call__(self, *args, **kwargs):
        return create_execution(self.dispatcher, *args, **kwargs)

    async def do(self, *args, **kwargs):
        async with self(*args, **kwargs) as execution:
            async for _ in execution:
                continue
            return execution.result

    async def get(self, *args, **kwargs):
        async with self(*args, **kwargs) as execution:
            output = []
            async for x in execution:
                output.append(x)
            return output

    async def close(self):
        await self.dispatcher.close()
