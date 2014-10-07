import sys

if sys.version_info < (2, 7):
    from unittest2 import main as test_main, SkipTest, TestCase
else:
    from unittest import main as test_main, SkipTest, TestCase

# Tests
# if env has changed since previous (e.g. conda install something,
# e.g. conda install ipython -p .tox/py26, get dep mismatch)


def test_test():
    pass

if __name__ == '__main__':
    test_main()
