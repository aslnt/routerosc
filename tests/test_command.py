from unittest import TestCase

from routerosc.command import dump_command

COMMANDS = [
    (['/x', {}, None, {}],
     [b'/x']),

    (['/x', {'a': b'0'}, ('=', 'b', b'1'), {'c': b'2'}],
     [b'/x', b'=a=0', b'?=b=1', b'.c=2']),

    (['/x', {'a': bytearray(b'0')}, ('=', 'b', bytearray(b'1')), {'c': bytearray(b'2')}],
     [b'/x', b'=a=0', b'?=b=1', b'.c=2']),

    (['/x', {'a': '0'}, ('=', 'b', '1'), {'c': '2'}],
     [b'/x', b'=a=0', b'?=b=1', b'.c=2']),

    (['/x', {'a': 0}, ('=', 'b', 1), {'c': 2}],
     [b'/x', b'=a=0', b'?=b=1', b'.c=2']),

    (['/x', {}, ('?', 'a'), {}],
     [b'/x', b'?a']),

    (['/x', {}, ('?-', 'a'), {}],
     [b'/x', b'?-a']),

    (['/x', {}, ('<', 'a', b'0'), {}],
     [b'/x', b'?<a=0']),

    (['/x', {}, ('=', 'a', b'0'), {}],
     [b'/x', b'?=a=0']),

    (['/x', {}, ('>', 'a', b'0'), {}],
     [b'/x', b'?>a=0']),

    (['/x', {}, ('!', ('?', 'a')), {}],
     [b'/x', b'?a', b'?#!']),

    (['/x', {}, ('|', ('?', 'a'), ('?', 'b'), ('?', 'c')), {}],
     [b'/x', b'?a', b'?b', b'?c', b'?#||']),

    (['/x', {}, ('&', ('?', 'a'), ('?', 'b'), ('?', 'c')), {}],
     [b'/x', b'?a', b'?b', b'?c', b'?#&&']),

    (['/x', {}, ('!=', 'a', b'0'), {}],
     [b'/x', b'?=a=0', b'?#!']),
]

BAD_COMMANDS = [
    ['', {}, None, {}],

    ['x', {}, None, {}],

    ['/x', {'': b'x'}, None, {}],

    ['/x', {}, ('?', ''), {}],

    ['/x', {}, None, {'': b'x'}],

    ['/x', {'=': b'x'}, None, {}],

    ['/x', {}, ('?', '='), {}],

    ['/x', {}, None, {'=': b'x'}],

    ['/x', {}, (), {}],
]


class DumpCommandTest(TestCase):
    def test(self):
        for command, sentence in COMMANDS:
            with self.subTest(command=command):
                self.assertEqual(dump_command(*command), sentence)

    def test_bad_command(self):
        for command in BAD_COMMANDS:
            with self.subTest(command=command):
                with self.assertRaises(ValueError):
                    dump_command(*command)
