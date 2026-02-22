from unittest import TestCase

from routerosc.reply import parse_reply

SENTENCES = [
    ([b'!x'],
     (b'!x', {}, {})),

    ([b'!x', b'=a=0', b'.b=1', b'=c=2'],
     (b'!x', {'a': b'0', 'c': b'2'}, {'b': b'1'})),

    ([b'!fatal', b'x'],
     (b'!fatal', b'x')),
]

BAD_SENTENCES = [
    [],

    [b''],

    [b'!'],

    [b'!x', b'x'],
]


class ParseReplyTest(TestCase):
    def test(self):
        for sentence, reply in SENTENCES:
            with self.subTest(sentence=sentence):
                self.assertEqual(parse_reply(sentence), reply)

    def test_bad_sentence(self):
        for sentence in BAD_SENTENCES:
            with self.subTest(sentence=sentence):
                with self.assertRaises(ValueError):
                    parse_reply(sentence)
