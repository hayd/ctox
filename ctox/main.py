"""This module defines the CLI for tox via main and ctox functions.

The Env class create the environment specific methods.

"""

import os
from ctox.shell import check_output, CalledProcessError  # TODO remove?

from ctox.shell import cprint

__version__ = version = '0.1.3'

SUPPORTED_ENVS = ('py26', 'py27', 'py33', 'py34', 'py35')


class Env(object):

    """A conda environment."""

    # TODO it's tempting to remove all but the tox variables as attributes
    # i.e. call out to pkg or config functions rather than dummy methods,
    # make the config and options private and have Env.ctox a function again.
    # This would makes the _replace_match substitution a little cleaner.

    def __init__(self, name, config, options, toxdir, toxinidir, package):
        self.config = config
        self.options = options
        self.name = name

        self.toxdir = toxdir
        self.toxinidir = toxinidir
        self.envdir = os.path.join(toxdir, self.name)
        self.distdir = os.path.join(self.toxdir, "dist")
        self.envdistdir = os.path.join(self.envdir, "dist")
        self.envctoxfile = os.path.join(self.envdir, "ctox")
        self.envbindir = os.path.join(self.envdir, "bin")

        self.conda = os.path.join(self.envbindir, "conda")
        self.pip = os.path.join(self.envbindir, "pip")
        self.python = os.path.join(self.envbindir, "python")
        self.envpython = self.python
        # TODO make this less of a hack
        # perhaps it should also be from basepython in config
        # should we use basepython as the variable name
        self.py_version = '.'.join(self.name[2:4])  # e.g. "2.7"

        # TODO think if package is correct, atm it's name + version
        # perhaps there is a proper tox name for this?
        self.package = package
        self.package_zipped = os.path.join(self.distdir,
                                           self.package + ".zip")
        self.envpackagedir = os.path.join(self.envdistdir, package)

        from ctox.config import (
            get_commands, get_deps, get_whitelist, get_changedir)
        self.changedir = get_changedir(self)
        # TODO remove these as attributes and call them directly
        self.whitelist = get_whitelist(self.config)
        self.deps = get_deps(self)
        self.commands = get_commands(self)

    def ctox(self):
        """Main method for the environment.

        Parse the tox.ini config, install the dependancies and run the
        commands. The output of the commands is printed.

        Returns 0 if they ran successfully, 1 if there was an error
        (either in setup or whilst running the commands), 2 if the build
        was skipped.

        """
        # TODO make this less of a hack e.g. using basepython from config
        # if it exists (and use an attribute directly).
        if self.name[:4] not in SUPPORTED_ENVS:
            from colorama import Style
            cprint(Style.BRIGHT +
                   "Skipping unsupported python version %s\n" % self.name,
                   'warn')
            return 2

        # TODO don't remove env if there's a dependancy mis-match
        # rather "clean" it to the empty state (the hope being to keep
        # the dist build around - so not all files need to be rebuilt)
        # TODO extract this as a method (for readability)
        if not self.env_exists() or self.reusableable():
            cprint("%s create: %s" % (self.name, self.envdir))
            self.create_env(force_remove=True)

            cprint("%s installdeps: %s" % (self.name, ', '.join(self.deps)))
            if not self.install_deps():
                cprint("    deps installation failed, aborted.\n", 'err')
                return 1
        else:
            cprint("%s cached (deps unchanged): %s" % (self.name, self.envdir))

        # install the project from the zipped file
        # TODO think more carefully about where it should be installed
        # specifically we want to be able this to include the test files (which
        # are not always unpacked when installed so as to run the tests there)
        # if there are build files (e.g. cython) then tests must run where
        # the build was. Also, reinstalling should not overwrite the builds
        # e.g. setup.py will skip rebuilding cython files if they are unchanged
        cprint("%s inst: %s" % (self.name, self.envdistdir))
        if not self.install_dist():
            cprint("    install failed.\n", 'err')
            return 1

        cprint("%s runtests" % self.name)
        # return False if all commands were successfully run
        # otherwise returns True if at least one command exited badly
        return self.run_commands()

    def prev_deps(self):
        from ctox.pkg import prev_deps
        return prev_deps(self)

    def reusableable(self):
        """Can we use the old environment.

        If this is True we don't need to
        create a new env and re-install the deps.

        """
        # TODO better caching !!
        # This should really make use of the conda + pip tree rather than just
        # rely on a crappy DIY csv. Part of the difficulty is that pip installs
        # have to be done seperately to conda, would be great to somehow merge
        # cleverly pip freeze? maybe needs to keep a clean env to compare with.
        return self.prev_deps() != self.deps

    def install_dist(self):
        from ctox.pkg import install_dist
        return install_dist(self)

    def install_deps(self):
        from ctox.pkg import install_deps
        return install_deps(self)

    def uninstall_deps(self, pdeps):
        # from ctox.pkg import uninstall_deps
        # return uninstall_deps(self, deps=pdeps)
        self.create_env(force_remove=True)

    def run_commands(self):
        from ctox.pkg import run_commands
        return run_commands(self)

    def env_exists(self):
        from ctox.pkg import env_exists
        return env_exists(self)

    def create_env(self, force_remove=False):
        from ctox.pkg import create_env
        return create_env(self, force_remove=force_remove)


def main(arguments, toxinidir=None):
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
        sys.exit(ctox(arguments, toxinidir))

    except CalledProcessError as c:
        print(c.output)
        return 1

    except NotImplementedError as e:
        gh = "https://github.com/hayd/ctox/issues"
        from colorama import Style
        cprint(Style.BRIGHT + str(e), 'err')
        cprint("If this is a valid tox.ini substitution, please open an issue on\n"
               "github and request support: %s." % gh, 'warn')
        return 1

    except KeyboardInterrupt:  # pragma: no cover
        return 1


def parse_args(arguments):
    from argparse import ArgumentParser
    description = ("Tox but with conda.")
    epilog = ("")
    parser = ArgumentParser(description=description,
                            epilog=epilog,
                            prog='ctox')
    parser.add_argument('--version',
                        help='print version number and exit',
                        action='store_true')
    parser.add_argument('-e',
                        help='choose environments to run, comma seperated',
                        default='ALL')

    return parser.parse_known_args(arguments)


def ctox(arguments, toxinidir):
    """Sets up conda environments, and sets up and runs each environment based
    on the project's tox.ini configuration file.

    Returns 1 if either the build or running the commands failed or 0 if
    all commmands ran successfully.

    """
    if arguments is None:
        arguments = []
    if toxinidir is None:
        toxinidir = os.getcwd()

    args, options = parse_args(arguments)

    if args.version:
        print(version)
        return 0

    # if no conda trigger OSError
    try:
        with open(os.devnull, "w") as fnull:
            check_output(['conda', '--version'], stderr=fnull)
    except OSError:
        cprint("conda not found, you need to install it to use ctox.\n"
               "The recommended way is to download miniconda,\n"
               "Do not install conda via pip.", 'err')
        return 1

    toxinifile = os.path.join(toxinidir, "tox.ini")

    from ctox.config import read_config, get_envlist
    config = read_config(toxinifile)
    if args.e == 'ALL':
        envlist = get_envlist(config)
    else:
        envlist = args.e.split(',')

    # TODO configure with option
    toxdir = os.path.join(toxinidir, ".tox")

    # create a zip file for the project
    from ctox.pkg import make_dist, package_name
    cprint("GLOB sdist-make: %s" % os.path.join(toxinidir, "setup.py"))
    package = package_name(toxinidir)
    if not make_dist(toxinidir, toxdir, package):
        cprint("    setup.py sdist failed", 'err')
        return 1

    # setup each environment and run ctox
    failing = {}
    for env_name in envlist:
        env = Env(name=env_name, config=config, options=options,
                  toxdir=toxdir, toxinidir=toxinidir, package=package)
        failing[env_name] = env.ctox()

    # print summary of the outcomes of ctox for each environment
    cprint('Summary')
    print("-" * 23)
    for env_name in envlist:
        n = failing[env_name]
        outcome = ('succeeded', 'failed', 'skipped')[n]
        status = ('ok', 'err', 'warn')[n]
        cprint("%s commands %s" % (env_name, outcome), status)

    return any(1 == v for v in failing.values())


def positional_args(arguments):
    """"Generator for position arguments.

    Example
    -------
    >>> list(positional_args(["arg1", "arg2", "--kwarg"]))
    ["arg1", "arg2"]
    >>> list(positional_args(["--", "arg1", "--kwarg"]))
    ["arg1", "kwarg"]

    """
    # TODO this behaviour probably isn't quite right.
    if arguments and arguments[0] == '--':
        for a in arguments[1:]:
            yield a
    else:
        for a in arguments:
            if a.startswith('-'):
                break
            yield a


def _main():
    "ctox: tox with conda"
    from sys import argv
    arguments = argv[1:]

    toxinidir = os.getcwd()

    return main(arguments, toxinidir)


if __name__ == '__main__':
    _main()
