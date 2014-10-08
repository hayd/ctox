import os
from ctox.shell import check_output, CalledProcessError  # TODO remove?

from ctox.shell import cprint

__version__ = version = '0.1.1a'

SUPPORTED_ENVS = ('py26', 'py27', 'py33', 'py34')

# 1. read in tox.ini file
# 2. create virtual envs (if they don't exist)
# 2a. check they are correct version ?
# 2b. cache installation (does conda just do that?)
# 3. install required stuff
# 4. run commands (need to flag if they are not from env?)


class Env(object):

    def __init__(self, name, config, options, toxdir, toxinidir):
        self.config = config
        self.options = options
        self.name = name

        self.toxinidir = toxinidir
        self.toxdir = toxdir
        self.envdir = os.path.join(toxdir, self.name)
        self.distdir = os.path.join(self.envdir, "dist")
        self.envdistdir = os.path.join(self.envdir, "dist")
        self.envctoxfile = os.path.join(self.envdir, "ctox")
        self.envbindir = os.path.join(self.envdir, "bin")

        self.conda = os.path.join(self.envbindir, "conda")
        self.pip = os.path.join(self.envbindir, "pip")
        self.python = os.path.join(self.envbindir, "python")
        py_version = '.'.join(self.name[2:4])  # e.g. "2.7"

        from ctox.config import get_commands, get_deps, get_whitelist
        self.whitelist = get_whitelist(self.config)
        self.deps = get_deps(
            self.name, self.config, self.toxdir, self.envbindir)
        self.commands = get_commands(self.name, self.config, self.envbindir)

    def ctox(self):
        """Main method for the envirnment.

        Parse the tox.ini config, install the dependancies and run the
        commands.

        """
        if self.name[:4] not in SUPPORTED_ENVS:
            from colorama import Style
            cprint(Style.BRIGHT +
                   "Skipping unsupported python version %s\n" % self.name,
                   '')
            return ''

        cprint("%s create: %s" % (self.name, self.envdir))
        if not self.env_exists():
            print("creating...")
            self.create_env(force_remove=True)

        cprint("%s installdeps: %s" % (self.name, ', '.join(self.deps)))
        pdeps = self.prev_deps()
        if pdeps != self.deps:
            self.uninstall_deps(pdeps)
            # TODO instead do a clean install?
            self.install_deps()

        cprint("%s inst: %s" % (self.name, self.envdistdir))
        self.install_dist()

        cprint("%s runtests" % self.name)
        # TODO move to run_tests
        return self.run_tests()

    def prev_deps(self):
        from ctox.pkg import prev_deps
        return prev_deps(self)

    def install_dist(self):
        from ctox.pkg import install_dist
        return install_dist(self)

    def install_deps(self):
        from ctox.pkg import install_deps
        return install_deps(self)

    def uninstall_deps(self, pdeps):
        from ctox.pkg import uninstall_deps
        return uninstall_deps(self, deps=pdeps)

    def run_tests(self):
        # TODO name change to run_commands
        from ctox.pkg import run_tests
        return run_tests(self)

    def env_exists(self):
        from ctox.pkg import env_exists
        return env_exists(self)

    def create_env(self, force_remove=False):
        from ctox.pkg import create_env
        return create_env(self, force_remove=force_remove)


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


def parse_args(arguments):
    from argparse import ArgumentParser
    description = ("Tox but with conda.")
    epilog = ("")
    parser = ArgumentParser(description=description,
                            epilog=epilog,
                            prog='pep8radius')
    parser.add_argument('--version',
                        help='print version number and exit',
                        action='store_true')
    return parser.parse_known_args(arguments)


def ctox(arguments, toxinidir):
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
               "Do not install conda via pip.", True)
        return 1

    toxinifile = os.path.join(toxinidir, "tox.ini")

    from ctox.config import read_config, get_envlist
    config = read_config(toxinifile)
    envlist = get_envlist(config)

    # TODO configure with option
    toxdir = os.path.join(toxinidir, ".tox")

    from ctox.pkg import make_dist
    cprint("GLOB sdist-make: %s" % os.path.join(toxinidir, "setup.py"))
    dist = make_dist(toxinidir, toxdir)

    failing = {}
    for env_name in envlist:
        env = Env(name=env_name, config=config, options=options,
                  toxdir=toxdir, toxinidir=toxinidir)
        failing[env_name] = env.ctox()

    cprint('Summary')
    print("-" * 23)
    for env_name in envlist:
        f = failing[env_name]
        res = ('failed' if f
               else 'skipped' if f is ''
               else 'succeeded')
        cprint("%s commands %s" % (env_name, res), f)

    return any(failing.values())


def _main(cwd=None):
    from sys import argv
    arguments = argv[1:]
    return main(arguments, None)


if __name__ == '__main__':
    _main()
