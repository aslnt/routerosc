async def send_sentence(writer, sentence):
    writer.write(encode_sentence(sentence))
    await writer.drain()


def encode_sentence(sentence):
    return b''.join(encode_word(x) for x in sentence) + b'\x00'


def encode_word(word):
    return encode_length(len(word)) + word


def encode_length(length):
    if not 0 != length < 0x100000000:
        raise ValueError(f"Bad length: {length!r}")

    if length >= 0x10000000:
        length |= 0xf000000000
    elif length >= 0x200000:
        length |= 0xE0000000
    elif length >= 0x4000:
        length |= 0xC00000
    elif length >= 0x80:
        length |= 0x8000

    return length.to_bytes((length.bit_length() + 7) // 8)


async def read_sentence(reader):
    sentence = []
    while word := await read_word(reader):
        sentence.append(word)
    return sentence


async def read_word(reader):
    return await reader.readexactly(await read_length(reader))


async def read_length(reader):
    byte = await reader.readexactly(1)

    if byte < b'\x80':
        return int.from_bytes(byte)
    if byte < b'\xc0':
        return int.from_bytes(byte + await reader.readexactly(1)) ^ 0x8000
    if byte < b'\xe0':
        return int.from_bytes(byte + await reader.readexactly(2)) ^ 0xC00000
    if byte < b'\xf0':
        return int.from_bytes(byte + await reader.readexactly(3)) ^ 0xE0000000
    if byte == b'\xf0':
        return int.from_bytes(await reader.readexactly(4))

    raise RuntimeError(f"Unexpected byte: {byte!r}")
