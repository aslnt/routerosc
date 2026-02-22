import re

NAME_RE = re.compile(r'/.+')
ATTRIBUTE_NAME_RE = re.compile(r'[^=]+')


def dump_command(name, attributes, query, api):
    try:
        if not NAME_RE.fullmatch(name):
            raise ValueError
        encoded_name = name.encode()
    except ValueError as e:
        raise ValueError(f"Bad command name: {name!r}") from e
    return [
        encoded_name,
        *dump_attributes(b'=', attributes),
        *(() if query is None else dump_query(query)),
        *dump_attributes(b'.', api),
    ]


def dump_attributes(prefix, attributes):
    for attribute in attributes.items():
        yield dump_attribute(prefix, *attribute)


def dump_attribute(prefix, name, value):
    return b''.join((prefix, dump_attribute_name(name), b'=', dump_attribute_value(value)))


def dump_attribute_name(name):
    try:
        if not ATTRIBUTE_NAME_RE.fullmatch(name):
            raise ValueError
        return name.encode()
    except ValueError as e:
        raise ValueError(f"Bad attribute name: {name!r}") from e


def dump_attribute_value(value):
    return value if isinstance(value, (bytearray, bytes)) else str(value).encode()


def dump_query(query):
    match query:
        case ['?' | '?-' as op, an]:
            yield op.encode() + dump_attribute_name(an)

        case ['<' | '=' | '>' as op, an, av]:
            yield dump_attribute(b'?' + op.encode(), an, av)

        case ['!', ex]:
            yield from dump_query(ex); yield b'?#!'

        case ['&' | '|' as op, *exs] if len(exs) > 1:
            for ex in exs: yield from dump_query(ex)
            yield b'?#' + op.encode() * (len(exs) - 1)

        case _:
            raise ValueError(f"Bad query: {query!r}")
