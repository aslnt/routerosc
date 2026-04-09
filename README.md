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


## API Reference


### `async connect(host, port=8728)`

Connects to a router and returns a [`Client`](#class-client) instance.

`host` is a string specifying the address of the router.

`port` is an integer specifying the network port number of the API service.


### `class Client`

Manages the connection and provides an interface for executing commands.


#### `Client` as an asynchronous context manager

[Closes](#async-clientclose) the client on exit from the block.


#### `async Client.do(command, attributes={}, query=None)`

Sends a command and returns the [result](#executionresult).

See [`Client.__call__()`](#async-client__call__command-attributes-querynone) for the meaning of `command`, `attributes` and `query`.


#### `async Client.get(command, attributes={}, query=None)`

Sends a command and returns the [output](#execution-as-an-asynchronous-iterator).

See [`Client.__call__()`](#async-client__call__command-attributes-querynone) for the meaning of `command`, `attributes` and `query`.


#### `async Client.__call__(command, attributes={}, query=None)`

Sends a command and returns an [`Execution`](#class-execution) instance.

`command` is a string specifying the command to execute (with slashes instead of spaces).

`attributes` is a dictionary mapping attribute names (strings) to values (any objects).

`query` is a [query expression](#query-expression) to filter the command output.


#### `async Client.close()`

Closes the connection.


### `class Execution`

Manages the command execution and provides access to its [output](#execution-as-an-asynchronous-iterator), [errors](#executionerrors) and [result](#executionresult).


#### `Execution` as an asynchronous context manager

[Closes](#async-executionclose) the execution on exit from the block.


#### `Execution` as an asynchronous iterator

Yields the command output as dictionaries mapping property names (strings) to values (byte strings).


#### `Execution.errors`

On failure, a list of errors (at least one); on success, an empty list.

An error is a dictionary containing: `"message"` — a byte string; `"category"` (optional) — a byte string.


#### `Execution.result`

On success, a dictionary mapping property names (strings) to values (byte strings); on failure, `None`.


#### `async Execution.close()`

Stops executing the command.


### `exception ServiceError`

Raised when the API service closes the connection due to an error.


#### `ServiceError.reason`

A byte string describing the error.


### `exception CommandError`

Raised when the command fails.


#### `CommandError.execution`

The failed [execution](#class-execution) (with at least one [error](#executionerrors)).


### Query expression

A boolean expression specified as a sequence where the first element is an operator and the remaining elements are operands.


#### Query expression operators

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
