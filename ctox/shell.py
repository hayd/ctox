"""This module contains light-weight wrappers to subprocess's check_output
and colored printing."""

from colorama import Fore, Style, init
from contextlib import contextmanager
import os
import sys

try:
    from StringIO import StringIO
except ImportError:  # py3, pragma: no cover
    # Note: although this would import in py2, io.StringIO is fussy about bytes
    # vs unicode, and this leads to pain.
    from io import StringIO


# https://github.com/hayd/pep8radius/blob/master/pep8radius/shell.py
try:
    from subprocess import STDOUT, check_output, CalledProcessError
except ImportError:  # pragma: no cover
    # python 2.6 doesn't include check_output
    # monkey patch it in!
    import subprocess
    STDOUT = subprocess.STDOUT

    def check_output(*popenargs, **kwargs):
        if 'stdout' in kwargs:  # pragma: no cover
            raise ValueError('stdout argument not allowed, '
                             'it will be overridden.')
        process = subprocess.Popen(stdout=subprocess.PIPE,
                                   *popenargs, **kwargs)
        output, _ = process.communicate()
        retcode = process.poll()
        if retcode:
            cmd = kwargs.get("args")
            if cmd is None:
                cmd = popenargs[0]
            raise subprocess.CalledProcessError(retcode, cmd,
                                                output=output)
        return output
    subprocess.check_output = check_output

    # overwrite CalledProcessError due to `output`
    # keyword not being available (in 2.6)
    class CalledProcessError(Exception):

        def __init__(self, returncode, cmd, output=None):
            self.returncode = returncode
            self.cmd = cmd
            self.output = output

        def __str__(self):
            return "Command '%s' returned non-zero exit status %d" % (
                self.cmd, self.returncode)
    subprocess.CalledProcessError = CalledProcessError


@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


def safe_shell_out(cmd, verbose=False, **kwargs):
    """run cmd and return True if it went ok, False if something went wrong.

    Suppress all output.

    """
    # TODO rename this suppressed_shell_out ?
    # TODO this should probably return 1 if there's an error (i.e. vice-versa).
    # print("cmd %s" % cmd)
    try:
        with open(os.devnull, "w") as fnull:
            with captured_output():
                check_output(cmd, stderr=fnull, **kwargs)
        return True
    except (CalledProcessError, OSError) as e:
        if verbose:
            cprint("    Error running command %s" % ' '.join(cmd), 'err')
            print(e.output)
        return False
    except Exception as e:
        # TODO no idea
        # Can this be if you try and unistall pip? (don't do that)
        return False


def shell_out(cmd, stderr=STDOUT, cwd=None):
    """Friendlier version of check_output."""
    if cwd is None:
        from os import getcwd
        cwd = getcwd()  # TODO do I need to normalize this on Windows
    out = check_output(cmd, cwd=cwd, stderr=stderr, universal_newlines=True)
    return _clean_output(out)


def _clean_output(out):
    try:
        out = out.decode('utf-8')
    except AttributeError:  # python3, pragma: no cover
        pass
    return out.strip()


def cprint(message, status=None):
    """color printing based on status:

    None -> BRIGHT
    'ok' -> GREEN
    'err' -> RED
    'warn' -> YELLOW

    """
    # TODO use less obscure dict, probably "error", "warn", "success" as keys
    status = {'warn': Fore.YELLOW, 'err': Fore.RED,
              'ok': Fore.GREEN, None: Style.BRIGHT}[status]
    print(status + message + Style.RESET_ALL)
