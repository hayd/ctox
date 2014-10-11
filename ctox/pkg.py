"""This module contains methods for installing and removing packages.

These are mostly lightweight wrappers shelling out to the conda and then
env.pip. Note that throughout this module the env variable is understood
to be a ctox.main.Env instance.

"""

import os

from subprocess import Popen, STDOUT
from ctox.shell import safe_shell_out, CalledProcessError, shell_out, cprint


def env_exists(env):
    return os.path.isdir(os.path.join(env.envdir, "conda-meta"))


def create_env(env, force_remove=False):
    # TODO cache cache cache!
    # TODO potentially we could keep a clean env around for each basepython.
    if force_remove:
        shell_out(['conda', 'remove', '-p', env.name, '--all',
                   '--yes', '--quiet'],
                  cwd=env.toxdir)

    shell_out(['conda', 'create', '-p', env.name,
               'python=%s' % env.py_version, '--yes', '--quiet'],
              cwd=env.toxdir)


def install(env, lib):
    lib_ = lib.replace('==', '=')  # obviously conda syntax is different
    success = (safe_shell_out(["conda", "install", lib_, "-p", env.name,
                               "--yes", "--quiet"], cwd=env.toxdir) or
               safe_shell_out([env.pip, "install",
                               "--quiet", lib], cwd=env.toxdir))

    if success:
        with open(env.envctoxfile, 'a') as f:
            f.write(" " + lib)
    else:
        cprint("    Unable to install %s." % lib, 'err')
    return success


def uninstall(env, lib):
    lib_ = lib.replace('==', '=')  # obviously conda syntax is different
    success = (safe_shell_out(["conda", "remove", lib_, "-p", env.name,
                               "--yes", "--quiet"], cwd=env.toxdir) or
               safe_shell_out([env.pip, "uninstall", lib,
                               "--yes", "--quiet"], cwd=env.toxdir))
    return success


def install_deps(env):
    print("installing deps...")
    try:
        # TODO can we do this in one pass?
        return all(install(env=env, lib=d) for d in env.deps)
    except (OSError, CalledProcessError) as e:
        import pdb
        pdb.set_trace()


def uninstall_deps(env, deps):
    # TODO actually use this.
    if deps:
        print("removing previous deps...")
        success = all(uninstall(env=env, lib=d) for d in deps[1:])
        if (not success) or deps[0] != "pip":
            cprint("    Environment dependancies mismatch, rebuilding.", 'err')
            create_env(env, force_remove=True)

    with open(env.envctoxfile, 'w') as f:
        f.write("")


def prev_deps(env):
    """Naively gets the dependancies from the last time ctox was run."""
    # TODO something more clever.
    if not os.path.isfile(env.envctoxfile):
        return []

    with open(env.envctoxfile) as f:
        return f.read().split()


def make_dist(toxinidir, toxdir, package):
    """zip up the package into the toxdir."""
    dist = os.path.join(toxdir, "dist")
    # Suppress warnings.
    success = safe_shell_out(["python", "setup.py", "sdist", "--quiet",
                              "--formats=zip", "--dist-dir", dist],
                             cwd=toxinidir)
    if success:
        return os.path.join(dist, package + ".zip")


def install_dist(env):
    # TODO don't rebuild if not changed?
    # At the moment entire dir is wiped, really we want to update, which would
    # allow us to reuse  previously built files (e.g. pyc) if unchanged...
    # This is usually done in the setup.py into a directory...
    print("installing...")
    return safe_shell_out([env.pip, "install", env.package_zipped,
                           "--no-deps", "--upgrade",
                           # "-t", env.envdistdir,
                           ],
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
    # Note: it's important all these tests are run, no short-circuiting.
    failing = any([run_one_command(env, c[:]) for c in env.commands])
    return failing


def run_one_command(env, command):
    # TODO move large part of this function to subst.parse_command.
    abbr_cmd, cmd, command = print_pretty_command(env, command)

    # Skip comments.
    line = " ".join(command).strip()
    if not line or line.startswith("#"):
        return 0

    # Ensure the command is already in envbindir or in the whitelist, correct
    # it if it's not in the whitelist (it'll OSError if it's not found).
    if cmd not in env.whitelist and not cmd.startswith(env.envbindir):
        command[0] = os.path.join(env.envbindir, cmd)

    # Run the command!
    try:
        p = Popen(command, cwd=env.changedir, stderr=STDOUT)
        p.communicate()
        return p.returncode
    except OSError as e:
        # Command not found locally (or not in whitelist).
        cprint("    OSError: %s" % e.args[1], 'err')
        cprint("    Is %s in dependancies or whitelist_externals?\n"
               % abbr_cmd,
               'warn')
        return 1


def print_pretty_command(env, command):
    """This is a hack for prettier printing.

    Rather than "{envpython} foo.py" we print "python foo.py".

    """
    cmd = abbr_cmd = command[0]
    if cmd.startswith(env.envbindir):
        abbr_cmd = os.path.relpath(cmd, env.envbindir)
        if abbr_cmd == ".":
            # TODO are there more edge cases?
            abbr_cmd = cmd
    command[0] = abbr_cmd
    print('(%s)$ %s' % (env.name, ' '.join(['"%s"' % c if " " in c
                                            else c
                                            for c in command])))
    command[0] = cmd
    return abbr_cmd, cmd, command
