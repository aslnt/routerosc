import functools


def promisify(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        return Promise(function(*args, **kwargs))
    return wrapper


class Promise:
    def __init__(self, coroutine):
        self.coroutine = coroutine

    def __await__(self):
        return self.coroutine.__await__()

    async def __aenter__(self):
        self.result = await self.coroutine
        return await self.result.__aenter__()

    async def __aexit__(self, *e):
        return await self.result.__aexit__(*e)
