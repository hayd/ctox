from tests.util import *

from ctox.main import *


# TODO not sure what we can unit test in main...
# For the moment we rely on integration testing.


class TestMain(TestCase):

    def test_positional_args(self):
        arguments = ['arg1', 'arg2', '--kwarg']
        res = list(positional_args(arguments))
        exp = ['arg1', 'arg2']
        self.assertEqual(res, exp)

    def test_positional_args_with_kwarg(self):
        arguments = ['--', 'arg1', '--kwarg']
        res = list(positional_args(arguments))
        exp = ['arg1', '--kwarg']
        self.assertEqual(res, exp)

    def test_parse_args_none(self):
        _, res = parse_args([])
        exp = []
        self.assertEqual(res, exp)

    def test_parse_args_some(self):
        _, res = parse_args(['arg', '--kwarg'])
        exp = ['arg', '--kwarg']
        self.assertEqual(res, exp)


if __name__ == '__main__':
    test_main()
