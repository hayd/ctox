from tests.util import *

from ctox.pkg import *

# TODO I'd quite like to test some of the create_env, install deps, etc.
# however I don't want to do this in each environment as creating, installing
# deps etc. is pretty slow. Perhap we could only run in in one env?


class TestPkg(TestCase):

    def test_print_pretty_command(self):
        from ctox.shell import captured_output
        env = DummyEnv(envbindir=TOXINIDIR, name="foo")
        command = [os.path.join(TOXINIDIR, "bar")]
        with captured_output() as (out, _):
            print_pretty_command(env, command)
        exp = "(foo)$ bar\n"
        self.assertEqual(out.getvalue(), exp)


if __name__ == '__main__':
    test_main()
