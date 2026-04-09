import asyncio
import sys

import routerosc

host, port, user, password = sys.argv[1:]


async def main():
    # connect to the service (and close the connection on exit from the block)
    async with routerosc.connect(host, port) as client:
        # log in to the service
        await client.do('/login', {'name': user, 'password': password})

        # execute the command and get the result
        print(await client.do('/file/add', {'name': 'test'}))

        # execute the command and get the output
        print(await client.get('/file/print', query=('!', ('=', 'type', 'directory'))))

        # execute the command and iterate over the output
        async with client('/file/print', query=('=', 'type', 'directory')) as execution:
            async for file in execution:
                print(file)

        # execute the long-running command (and stop the execution on exit from the block)
        async with client('/log/listen') as execution:
            async for entry in execution:
                print(entry)
                if entry['message'] == b'stop':
                    break

        # execute the commands concurrently through the same connection
        print(await asyncio.gather(*(
            client.get('/ping', {'count': 1, 'address': f'192.168.88.{x}'})
            for x in range(1, 10)
        )))


asyncio.run(main())
