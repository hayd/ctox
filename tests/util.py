import os
import sys

if sys.version_info < (2, 7):
    from unittest2 import main as test_main, SkipTest, TestCase
else:
    from unittest import main as test_main, SkipTest, TestCase

from ctox.main import Env

TOXINIDIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
TOXINIFILE = os.path.join(TOXINIDIR, "tox.ini")


class DummyEnv(Env):

    "Bunch dummy environment."

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
