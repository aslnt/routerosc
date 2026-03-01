# routerosc

An asynchronous Python client for MikroTik RouterOS API.


## Example

```python
# connect to the service (and close the connection on exit from the block)
async with routerosc.connect(host, port) as client:
    # log in to the service
    await client.do('/login', {'name': user, 'password': password})

    try:
        # execute the command and get the result
        print(await client.do('/file/add', {'name': 'test'}))
    except routerosc.CommandError as e:
        print(e)

    # execute the command and get the output
    print(await client.get('/file/print', query=('!', ('=', 'type', 'directory'))))

    # execute the command and iterate over the output
    async with client('/file/print', query=('=', 'type', 'directory')) as execution:
        async for file in execution:
            print(file)

    # cancel the execution on exit from the block
    async with client('/log/listen') as execution:
        async for entry in execution:
            if entry['message'] == b'test':
                print(entry)
                break

    # execute the commands concurrently (through the same connection)
    print(await asyncio.gather(*(
        client.get('/ping', {'count': 1, 'address': f'192.168.88.{x}'})
        for x in range(1, 10)
    )))

    # more of the same
    async with asyncio.TaskGroup() as g:
        async with client('/ip/dns/static/listen') as execution:
            async for entry in execution:
                if not entry.get('.dead') and not entry.get('comment'):
                    g.create_task(client.do('/ip/dns/static/set', {
                        '.id': entry['.id'], 'comment': 'test',
                    }))
```
