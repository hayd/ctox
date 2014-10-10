"""This module contains methods for installing and removing packages.

These are mostly lightweight wrappers shelling out to the conda and then
env.pip. Note that throughout this module the env variable is understood
to be a ctox.main.Env instance.

"""

import os

from ctox.shell import safe_shell_out, CalledProcessError, shell_out, cprint


def env_exists(env):
    return os.path.isdir(os.path.join(env.envdir, "conda-meta"))


def create_env(env, force_remove=False):
    # TODO cache cache cache!

    if force_remove:
        shell_out(['conda', 'remove', '-p', env.name, '--all',
                   '--yes', '--quiet'],
                  cwd=env.toxdir)

    shell_out(['conda', 'create', '-p', env.name,
               'python=%s' % env.py_version, '--yes', '--quiet'],
              cwd=env.toxdir)


def install(lib, env):
    lib_ = lib.replace('==', '=')  # obviously conda syntax is different
    success = (safe_shell_out(["conda", "install", lib_, "-p", env.name,
                               "--yes", "--quiet"], cwd=env.toxdir) or
               safe_shell_out([env.pip, "install",
                               "--quiet", lib], cwd=env.toxdir))

    if success:
        with open(env.envctoxfile, 'a') as f:
            f.write(" " + lib)
    else:
        cprint("    Unable to install %s." % lib, True)
    return success


def uninstall(lib, env):
    lib_ = lib.replace('==', '=')  # obviously conda syntax is different
    success = (safe_shell_out(["conda", "remove", lib_, "-p", env.name,
                               "--yes", "--quiet"], cwd=env.toxdir) or
               safe_shell_out([env.pip, "uninstall", lib,
                               "--yes", "--quiet"], cwd=env.toxdir))
    return success


def install_deps(env):
    print("installing deps...")
    try:
        return all(install(d, env=env) for d in env.deps)
        ##conda = os.path.join(cwd, env, "bin", "conda")
        # check_output(['conda', 'install', '-p', env, '--yes', '--quiet'] + deps,
        #             cwd=cwd)
    except (OSError, CalledProcessError) as e:
        import pdb
        pdb.set_trace()


def uninstall_deps(env, deps):
    if deps:
        print("removing previous deps...")
        # Note: deps
        success = all(uninstall(d, env=env) for d in deps[1:])
        if (not success) or deps[0] != "pip":
            cprint("    Environment dependancies mismatch, rebuilding.", True)
            create_env(env, force_remove=True)

    with open(env.envctoxfile, 'w') as f:
        f.write("")


def prev_deps(env):
    "Naively gets the dependancies from the last time ctox was run."
    if not os.path.isfile(env.envctoxfile):
        return []

    with open(env.envctoxfile) as f:
        return f.read().split()


def make_dist(toxinidir, toxdir, package):
    "zip up the package into the toxdir"
    dist = os.path.join(toxdir, "dist")
    # suppress warnings
    success = safe_shell_out(["python", "setup.py", "sdist", "--quiet",
                              "--formats=zip", "--dist-dir", dist],
                             cwd=toxinidir)
    if success:
        return os.path.join(dist, package + ".zip")


def install_dist(env):
    # TODO don't rebuild if not changed?
    # at the moment entire dir is wiped, really we want to update, which would
    # allow us to reuse  previously built files (e.g. pyc) if unchanged...
    # this is usually done in the setup.py into a directory...
    print("installing...")
    return safe_shell_out([env.pip, "install", env.package_zipped,
                              "--no-deps", "--upgrade"],  # , "-t", env.envdistdir],
                             cwd=env.toxdir)

    # from zipfile import ZipFile
    # with ZipFile(env.package_zipped, "r") as z:
    #     z.extractall(env.envdistdir)
    # return safe_shell_out([env.python, "setup.py", "install"],  # --no-deps
    #                       cwd=env.envpackagedir)


def package_name(toxinidir):
    return '-'.join(shell_out(["python", "setup.py", "--name", "--version"],
                              cwd=toxinidir).split())


def run_commands(env):
    # Note: it's important all these tests are run, no short-circuiting
    failing = any([run_one_command(env, c[:]) for c in env.commands])
    return failing


def run_one_command(env, command):
    # this is a hack for prettier printing
    cmd = _cmd = command[0]
    if cmd.startswith(env.envbindir):
        _cmd = os.path.relpath(cmd, env.envbindir)
        if _cmd == ".":
            _cmd = cmd
    command[0] = _cmd
    print('(%s)$ %s' % (env.name, ' '.join(['"%s"' % c if " " in c
                                            else c
                                            for c in command])))
    command[0] = cmd

    # skip comments
    line = " ".join(command).strip()
    if not line or line.startswith("#"):
        return False

    if cmd not in env.whitelist and not cmd.startswith(env.envbindir):
        command[0] = os.path.join(env.envbindir, cmd)
    try:
        print(shell_out(command, cwd=env.changedir))
        return False
    except OSError as e:
        # TODO question whether command is installed locally?
        cprint("    OSError: %s" % e.args[1], True)
        cprint("    Is %s in your dependancies?\n" % cmd, True)
        return True
    except Exception as e:  # TODO should we captured_output ?
        import pdb
        pdb.set_trace()
        return True
