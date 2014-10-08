from colorama import Fore, Style, init
from contextlib import contextmanager
import os
from subprocess import CalledProcessError, check_output
import sys

try:
    from io import StringIO
except ImportError:  # py2, pragma: no cover
    from StringIO import StringIO


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
    #print("cmd %s" % cmd)
    try:
        with open(os.devnull, "w") as fnull:
            with captured_output() as (out, err):
                check_output(cmd, stderr=fnull, **kwargs)
        return True
    except (CalledProcessError, OSError) as e:
        if verbose:
            cprint("    Error running command %s" % ' '.join(cmd),
                   True)
            print(e.output)
        return False
    except Exception as e:
        # TODO no idea
        # Can this be if you try and unistall pip? (don't do that)
        return False


def cprint(message, status=None):
    """color printing based on status:

    None -> BRIGHT
    False -> GREEN
    True -> RED
    '' -> YELLOW

    """
    init(autoreset=True)
    status = {'': Fore.YELLOW, True: Fore.RED,
              False: Fore.GREEN, None: Style.BRIGHT}[status]
    print(status + message)
