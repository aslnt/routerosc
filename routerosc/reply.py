import re

REPLY_WORD_RE = re.compile(br'!.+')
ATTRIBUTE_WORD_RE = re.compile(br'(?s)([.=])([^=]+)=(.*)')


def parse_reply(sentence):
    match sentence:
        case [b'!fatal', reason]:
            return tuple(sentence)
        case [reply_word, *words] if REPLY_WORD_RE.fullmatch(reply_word):
            return (reply_word, *parse_attributes(words))
        case _:
            raise ValueError


def parse_attributes(words):
    attributes = {}
    api_attributes = {}
    for word in words:
        prefix, name, value = parse_attribute(word)
        (attributes if prefix == b'=' else api_attributes)[name] = value
    return attributes, api_attributes


def parse_attribute(word):
    try:
        prefix, name, value = ATTRIBUTE_WORD_RE.fullmatch(word).groups()
    except AttributeError:
        raise ValueError from None
    return prefix, name.decode(), value
