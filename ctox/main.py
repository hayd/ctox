from colorama import Fore, Style, init
from contextlib import contextmanager
import re
import os
import signal
import shutil
try:
    from io import StringIO
except ImportError:  # py2, pragma: no cover
    from StringIO import StringIO

from subprocess import check_output, CalledProcessError, PIPE
import sys

try:
    from configparser import ConfigParser as SafeConfigParser, NoSectionError, NoOptionError
except ImportError:  # py2, pragma: no cover
    from ConfigParser import SafeConfigParser, NoSectionError, NoOptionError

__version__ = version = '0.1a'

SUPPORTED_ENVS = ('py26', 'py27', 'py33', 'py34')

# 1. read in tox.ini file
# 2. create virtual envs (if they don't exist)
# 2a. check they are correct version ?
# 2b. cache installation (does conda just do that?)
# 3. install required stuff
# 4. run commands (need to flag if they are not from env?)


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
    try:
        with open(os.devnull, "w") as fnull:
            with captured_output() as (out, err):
                check_output(cmd, stderr=fnull, **kwargs)
        return True
    except (CalledProcessError, OSError) as e:
        if verbose:
            cprint("    Error running command %s" % ' '.join(cmd),
                   True)
            print(e)
        return False
    except Exception:
        import pdb
        pdb.set_trace()


def main(arguments=None, cwd=None):
    "ctox: tox with conda."
    try:  # pragma: no cover
        # Exit on broken pipe.
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except AttributeError:  # pragma: no cover
        # SIGPIPE is not available on Windows.
        pass

    try:
        sys.exit(ctox(arguments, cwd))

    except CalledProcessError as c:
        print(c.output)
        return 1

    except KeyboardInterrupt:  # pragma: no cover
        return 1


def install(lib, cwd, env):
    pip = os.path.join(cwd, env, "bin", "pip")
    success = (safe_shell_out(["conda", "install", lib, "-p", env,
                               "--yes", "--quiet"], cwd=cwd) or
               safe_shell_out([pip, "install",
                               "--quiet", lib], cwd=cwd))

    if success:
        with open(os.path.join(cwd, env, "ctox"), 'a') as f:
            f.write(" " + lib)
    return success


def uninstall(lib, cwd, env):
    pip = os.path.join(cwd, env, "bin", "pip")
    success = (safe_shell_out(["conda", "remove", lib, "-p", env,
                               "--yes", "--quiet"]) or
               safe_shell_out([pip, "uninstall", lib,
                               "--quiet"]))
    return success


def ctox(arguments, cwd):
    if arguments is None:
        arguments = []
    if cwd is None:
        cwd = os.getcwd()
    #args = parse_args(arguments)

    # if no conda trigger OSError
    try:
        with open(os.devnull, "w") as fnull:
            check_output(['conda', '--version'], stderr=fnull)
    except OSError:
        cprint("conda not found, you need to install it to use ctox.\n"
               "The recommended way is to download miniconda,\n"
               "Do not install conda via pip.", True)
        return 1

    config = read_config(cwd)
    envlist = get_envlist(config)

    parent = cwd
    cwd = os.path.join(cwd, ".tox")

    cprint("GLOB sdist-make: %s" % os.path.join(parent, "setup.py"))
    dist = make_dist(parent, cwd)  # TODO configure with option

    failing = {}
    for env in envlist:
        failing[env] = ctox_env(env, config, cwd, parent=parent, dist=dist)

    cprint('Summary')
    print("-" * 23)
    for env in envlist:
        f = failing[env]
        res = ('failed' if f
               else 'skipped' if f is ''
               else 'succeeded')
        cprint("%s commands %s" % (env, res), f)

    return any(failing.values())


def ctox_env(env, config, cwd, dist, parent):
    init(autoreset=True)
    if env not in SUPPORTED_ENVS:
        cprint(
            Style.BRIGHT + "Skipping unsupported python version %s\n" % env, '')
        return ''

    path = os.path.join('.tox', env)
    cprint("%s create: %s" % (env, path))
    if not env_exists(env, cwd):
        print("creating...")
        create_env(env, cwd, force_remove=True)

    deps = get_deps(env, config)
    cprint("%s installdeps: %s" % (env, ', '.join(deps)))
    pdeps = prev_deps(env, cwd)
    if pdeps != deps:
        uninstall_deps(env, pdeps, cwd)
        install_deps(env, deps, cwd)

    cprint("%s inst: %s" % (env, dist))
    install_dist(env, cwd, dist=dist)

    cprint("%s runtests" % env)
    commands = get_commands(env, config)
    return run_test(env, commands, cwd, parent=parent)


def read_config(cwd):
    tox_file = os.path.join(cwd, 'tox.ini')

    config = SafeConfigParser()
    config.read(tox_file)

    return config


def _get(config, *args):
    try:
        return config.get(*args)
    except (NoSectionError, NoOptionError):
        return ''


def get_envlist(config):
    return _get(config, 'tox', 'envlist').split(',')


def get_deps(env, config):
    deps = _get(config, 'testenv', 'deps').split()
    env_deps = _get(config, 'testenv:%s' % env, 'deps').split()
    return [d for d in ["pip"] + deps + env_deps
            if not re.match("conda([=<>!]|$)", d)]


def create_env(env, cwd, force_remove=False):
    py_version = '.'.join(env[2:])
    # TODO cache cache cache!

    if force_remove:
        check_output(['conda', 'remove', '-p', env, '--all',
                      '--yes', '--quiet'],
                     cwd=cwd)

    check_output(['conda', 'create', '-p', env,
                  'python=%s' % py_version, '--yes', '--quiet'],
                 cwd=cwd)


def env_exists(env, cwd):
    return os.path.isdir(os.path.join(cwd, env, "conda-meta"))


def install_deps(env, deps, cwd):
    print("installing deps...")
    try:
        return all(install(d, env=env, cwd=cwd) for d in deps)
        ##conda = os.path.join(cwd, env, "bin", "conda")
        # check_output(['conda', 'install', '-p', env, '--yes', '--quiet'] + deps,
        #             cwd=cwd)
    except (OSError, CalledProcessError) as e:
        import pdb
        pdb.set_trace()


def uninstall_deps(env, deps, cwd):
    if deps:
        print("removing previous deps...")
        success = all(uninstall(d, env=env, cwd=cwd) for d in deps)
        if not success:
            cprint("    Environment dependancies mismatch, rebuilding.", True)
            create_env(env, cwd, force_remove=True)
    c = os.path.join(cwd, env, "ctox")

    with open(c, 'w') as f:
        f.write("")


def prev_deps(env, cwd):
    c = os.path.join(cwd, env, "ctox")
    if not os.path.isfile(c):
        return []

    with open(c) as f:
        return f.read().split()

    # with open(os.path.join(cwd, env, "conda-meta", "history")) as history:
    # for line in (line for line in history if line.startswith("# cmd:")):
    #         pass
    # try:
    # Note: it could be this line is complete nonsense
    # for example if the command does not contain --quiet
    # in which case this will be caught later
    #     return line.split('--quiet')[-1].strip().split()
    # except NameError:  # first time or history cleared
    #     return []


def install_dist(env, cwd, dist):
    # TODO don't rebuild if not changed?
    print("installing...")
    pip = os.path.join(cwd, env, "bin", "pip")
    local_dist = os.path.join(cwd, env, "dist")
    safe_shell_out([pip, "install", dist, "--no-clean", "--no-deps", "-t", local_dist],
                   cwd=cwd)


def get_commands(env, config):
    # TODO allow for running over new lines? Is this correct at all?
    commands = _get(config, 'testenv', 'commands').split("\n")
    env_commands = _get(config, 'testenv:%s' % env, 'commands').split("\n")
    return [cmd.split() for cmd in commands + env_commands if cmd]


def make_dist(parent, cwd):
    dist = os.path.join(cwd, "dist")
    # suppress warnings
    with open(os.devnull, "w") as fnull:
        check_output(["python", "setup.py", "sdist", "--quiet",
                      "--formats=zip", "--dist-dir", dist],
                     stderr=fnull, cwd=parent)
    v = '-'.join(check_output(["python", "setup.py", "--name", "--version"],
                              cwd=parent).split())
    return os.path.join(dist, v) + ".zip"


def run_test(env, commands, cwd, parent):
    failing = False
    for command in commands:
        # TODO make sure in env better!!
        # prepend env to first command
        print('(%s) "%s"' % (env, ' '.join(command)))
        cmd = command[0]
        command[0] = os.path.join(cwd, env, 'bin', cmd)
        try:
            print(check_output(command, cwd=parent))
        except OSError as e:
            # TODO question whether command is installed locally?
            cprint("    OSError: %s" % e.args[1], True)
            cprint("    Is %s in your dependancies?\n" % cmd, True)
            failing = True
        except Exception as e:  # TODO should we captured_output ?
            failing = True
    return failing


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


if __name__ == '__main__':
    main(None, None)
