from tests.util import *

from ctox.config import *


class TestConfig(TestCase):

    config = read_config(TOXINIFILE)

    def test_get_whitelist(self):
        res = get_whitelist(self.config)
        self.assertEqual(res, ["echo"])

    def test_get_changedir(self):
        env = DummyEnv(name="py26", config=self.config, envdir="foo")
        res = get_changedir(env)
        self.assertEqual(res, "foo")

    def test_get_envlist(self):
        res = get_envlist(self.config)
        exp = ['py26', 'py27', 'py33-unify', 'py34-unify', 'foo']
        self.assertEqual(res, exp)

    def test_get_deps(self):
        env = DummyEnv(name="py26", config=self.config)
        res = get_deps(env)
        exp = ['pip', 'argparse', 'unittest2', 'nose', 'colorama', 'pyfaker']
        self.assertEqual(res, exp)

    # TODO def test_get_commands (too unstable atm)


if __name__ == '__main__':
    test_main()
