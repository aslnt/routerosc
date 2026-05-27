# routerosc

An asynchronous Python client for MikroTik RouterOS API.


## Installation

```shell
pip install git+https://github.com/aslnt/routerosc.git
```


## Usage

```python
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
```


## API reference

- [`connect()`](#connect)
- [`class Client`](#class-client)
- [`class Execution`](#class-execution)
- [`exception CommandError`](#exception-commanderror)
- [`exception ServiceError`](#exception-serviceerror)
- [Query expression](#query-expression)
- [Encoding](#encoding)


### `connect()`

`def connect(host, port=8728, *, queue_size=10): ...`

Connects to a router and returns a [`Client`](#class-client) instance when awaited or used with `async with`.

`host` is the domain name or IPv4/v6 address of the router.

`port` is the network port number of the API service.

`queue_size` is the maximum number of replies queued per command before backpressure takes effect.


### `class Client`

Manages the connection and provides an interface for executing commands.


#### `Client` as an asynchronous context manager

[Closes](#clientclose) the client on exit from the block.


#### `Client.do()`

`async def do(self, command, attributes={}, query=None): ...`

Sends a command and returns the [result](#executionresult).

See [`Client.__call__()`](#client__call__) for the meaning of `command`, `attributes` and `query`.


#### `Client.get()`

`async def get(self, command, attributes={}, query=None): ...`

Sends a command and returns the [output](#execution-as-an-asynchronous-iterator).

See [`Client.__call__()`](#client__call__) for the meaning of `command`, `attributes` and `query`.


#### `Client.__call__()`

`def __call__(self, command, attributes={}, query=None): ...`

Sends a command and returns an [`Execution`](#class-execution) instance when awaited or used with `async with`.

`command` is a string specifying the command to execute (with slashes instead of spaces).

`attributes` is a dictionary mapping attribute names (strings) to values (of any type).

`query` is a [query expression](#query-expression) used to filter the command output.

See [Encoding](#encoding) for details on how data is encoded before sending.


#### `Client.close()`

`async def close(self): ...`

Closes the connection.


### `class Execution`

Manages the command execution and provides access to its [output](#execution-as-an-asynchronous-iterator), [errors](#executionerrors) and [result](#executionresult).


#### `Execution` as an asynchronous context manager

[Closes](#executionclose) the execution on exit from the block.


#### `Execution` as an asynchronous iterator

Yields the command output as dictionaries mapping property names (strings) to values (byte strings).


#### `Execution.errors`

On failure, a list of errors (at least one); on success, an empty list.

An error is a dictionary containing: `"message"` — a byte string; `"category"` (optional) — a byte string.


#### `Execution.result`

On success, a dictionary mapping property names (strings) to values (byte strings); on failure, `None`.


#### `Execution.close()`

`async def close(self): ...`

Stops executing the command (sends an additional (control) command).


### `exception CommandError`

Raised when a command fails.


#### `CommandError.execution`

The failed [execution](#class-execution) (with at least one [error](#executionerrors)).


### `exception ServiceError`

Raised when an API service closes the connection due to an error.


#### `ServiceError.reason`

A byte string describing the error.


### Query expression

A boolean expression specified as a sequence where the first element is an operator and the remaining elements are operands.


#### Query operators

* `('?', property)` — whether `property` is set
* `('?-', property)` — whether `property` is not set
* `('=', property, value)` — whether `property` is equal to `value`
* `('!=', property, value)` — whether `property` is not equal to `value`
* `('<', property, value)` — whether `property` is less than `value`
* `('>', property, value)` — whether `property` is greater than `value`
* `('<=', property, value)` — whether `property` is less than or equal to `value`
* `('>=', property, value)` — whether `property` is greater than or equal to `value`
* `('!', expression)` — whether `expression` is `False`
* `('&', *expressions)` — whether all of `expressions` are `True`
* `('|', *expressions)` — whether any of `expressions` is `True`

where:
- `property` is a string specifying the property name
- `value` is an object of any type specifying the property value

See [Encoding](#encoding) for details on how data is encoded before sending.


### Encoding

Byte strings are sent as-is; other objects are converted to strings and encoded using UTF-8.
