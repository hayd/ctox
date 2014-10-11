from tests.util import *

from ctox.subst import *


class TestSubst(TestCase):

    def test_parse_envlist(self):
        # simple example is same as bash_expand
        s = "{py26,py27}-django{15,16}, py32"
        res = parse_envlist(s)
        exp = ["py26-django15", "py26-django16", "py27-django15",
               "py27-django16", "py32"]
        self.assertEqual(res, exp)

    def test_parse_bash_expand(self):
        s = "{py26,py27}-django{15,16}, py32"
        res = parse_envlist(s)
        exp = ["py26-django15", "py26-django16", "py27-django15",
               "py27-django16", "py32"]
        self.assertEqual(res, exp)

    def test_expand_curlys(self):
        res = expand_curlys("py{26, 27}")
        exp = ["py26", "py27"]
        self.assertEqual(res, exp)

    def test_expand_curlys_two(self):
        res = expand_curlys("py{26, 27}-django{15, 16}")
        exp = ["py26-django15", "py26-django16", "py27-django15",
               "py27-django16"]
        self.assertEqual(res, exp)

    def test_expand_factor_conditions_match(self):
        env = DummyEnv(name='py33')
        s = 'py{33,34}: docformatter'
        res = expand_factor_conditions(s, env)
        exp = "docformatter"
        self.assertEqual(res, exp)

    def test_expand_factor_conditions_mismatch(self):
        env = DummyEnv(name='py26')
        s = 'py{33,34}: docformatter'
        res = expand_factor_conditions(s, env)
        exp = ""
        self.assertEqual(res, exp)

    def test_matches_factor_conditions_match(self):
        env = DummyEnv(name='py34')
        s = "py{33, 34}"
        res = matches_factor_conditions(s, env)
        self.assertTrue(res)

    def test_matches_factor_conditions_mismatch(self):
        env = DummyEnv(name='py26')
        s = "py{33, 34}"
        res = matches_factor_conditions(s, env)
        self.assertFalse(res)

    def test_split_on(self):
        s = "a,b,'c,d'"
        res = split_on(s, ',')
        exp = ['a', 'b', 'c,d']
        self.assertEqual(res, exp)

    def test_split_on_triple(self):
        s = "a,b,'''c,d'''"
        res = split_on(s, ',')
        exp = ['a', 'b', 'c,d']
        self.assertEqual(res, exp)


class TestReplaceBraces(TestCase):

    def test_replace_braces_attr(self):
        env = DummyEnv(toxdir="foo")
        s = "{toxdir}"
        res = replace_braces(s, env)
        self.assertEqual(res, "foo")

    def test_replace_braces_envvar(self):
        env = DummyEnv()
        s = "{env:USER:}"
        res = replace_braces(s, env)
        exp = os.environ.get("USER", "")
        self.assertEqual(res, exp)

    def test_replace_braces_envvar_missing_default(self):
        if os.environ.get("NOTAENVKEY", ""):
            raise SkipTest()

        env = DummyEnv()
        s = "{env:NOTAENVKEY:}"
        res = replace_braces(s, env)
        self.assertEqual(res, "")

    def test_replace_braces_envvar_missing(self):
        if os.environ.get("NOTAENVKEY", ""):
            raise SkipTest()

        env = DummyEnv()
        s = "{env:NOTAENVKEY}"
        self.assertRaises(KeyError, replace_braces, s, env)

    def test_replace_braces_config(self):
        from ctox.config import read_config
        config = read_config(TOXINIFILE)
        env = DummyEnv(config=config)
        s = "{[base]ment}"
        res = replace_braces(s, env)
        self.assertEqual(res.strip(), "pyfaker")

    def test_replace_braces_posargs(self):
        env = DummyEnv(options=['arg1', 'arg2'])
        s = "{posargs:no posargs passed}"
        res = replace_braces(s, env)
        exp = "arg1 arg2"
        self.assertEqual(res, exp)

    def test_replace_braces_no_posargs(self):
        env = DummyEnv(options=[])
        s = "{posargs:no posargs passed}"
        res = replace_braces(s, env)
        exp = "no posargs passed"
        self.assertEqual(res, exp)


if __name__ == '__main__':
    test_main()
