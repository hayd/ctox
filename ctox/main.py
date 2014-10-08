import os
from ctox.shell import check_output, CalledProcessError  # TODO remove?

from ctox.shell import cprint

__version__ = version = '0.1'

SUPPORTED_ENVS = ('py26', 'py27', 'py33', 'py34')

# 1. read in tox.ini file
# 2. create virtual envs (if they don't exist)
# 2a. check they are correct version ?
# 2b. cache installation (does conda just do that?)
# 3. install required stuff
# 4. run commands (need to flag if they are not from env?)


def main(arguments=None, cwd=None):
    "ctox: tox with conda."
    try:  # pragma: no cover
        # Exit on broken pipe.
        import signal
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except AttributeError:  # pragma: no cover
        # SIGPIPE is not available on Windows.
        pass

    try:
        import sys
        sys.exit(ctox(arguments, cwd))

    except CalledProcessError as c:
        print(c.output)
        return 1

    except NotImplementedError as e:
        gh = "https://github.com/hayd/ctox/issues"
        from colorama import Style
        cprint(Style.BRIGHT + str(e), True)
        cprint("If this is a valid tox.ini substitution, please open an issue on\n"
               "github and request support: %s." % gh, '')
        return 1

    except KeyboardInterrupt:  # pragma: no cover
        return 1


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

    from ctox.config import read_config, get_envlist
    config = read_config(cwd)
    envlist = get_envlist(config)

    parent = cwd
    cwd = os.path.join(cwd, ".tox")

    from ctox.pkg import make_dist
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
    from ctox.pkg import (create_env, env_exists, prev_deps, install_deps,
                          uninstall_deps, install_dist, run_tests)
    from ctox.config import get_deps
    deps = get_deps(env, config)

    if env[:4] not in SUPPORTED_ENVS:
        from colorama import Style
        cprint(Style.BRIGHT + "Skipping unsupported python version %s\n" % env,
               '')
        return ''

    path = os.path.join('.tox', env)
    cprint("%s create: %s" % (env, path))
    if not env_exists(env, cwd):
        print("creating...")
        create_env(env, cwd, force_remove=True)

    cprint("%s installdeps: %s" % (env, ', '.join(deps)))
    pdeps = prev_deps(env, cwd)
    if pdeps != deps:
        uninstall_deps(env, pdeps, cwd)
        install_deps(env, deps, cwd)

    cprint("%s inst: %s" % (env, dist))
    install_dist(env, cwd, dist=dist)

    cprint("%s runtests" % env)
    # TODO move to run_tests
    from ctox.config import get_commands, get_whitelist
    commands = get_commands(env, config)
    whitelist = get_whitelist(config)
    return run_tests(env, commands, cwd, parent=parent, whitelist=whitelist)


if __name__ == '__main__':
    main(None, None)
