import os

from ctox.shell import safe_shell_out, CalledProcessError, shell_out, cprint


def install(lib, env):
    success = (safe_shell_out(["conda", "install", lib, "-p", env.name,
                               "--yes", "--quiet"], cwd=env.toxdir) or
               safe_shell_out([env.pip, "install",
                               "--quiet", lib], cwd=env.toxdir))

    if success:
        with open(env.envctoxfile, 'a') as f:
            f.write(" " + lib)
    return success


def uninstall(lib, env):
    success = (safe_shell_out(["conda", "remove", lib, "-p", env.name,
                               "--yes", "--quiet"], cwd=env.toxdir) or
               safe_shell_out([env.pip, "uninstall", lib,
                               "--yes", "--quiet"], cwd=env.toxdir))
    return success


def create_env(env, force_remove=False):
    # TODO cache cache cache!

    if force_remove:
        shell_out(['conda', 'remove', '-p', env.name, '--all',
                   '--yes', '--quiet'],
                  cwd=env.toxdir)

    shell_out(['conda', 'create', '-p', env.name,
               'python=%s' % env.py_version, '--yes', '--quiet'],
              cwd=env.toxdir)


def env_exists(env):
    return os.path.isdir(os.path.join(env.envdir, "conda-meta"))


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
    if not os.path.isfile(env.envctoxfile):
        return []

    with open(env.envctoxfile) as f:
        return f.read().split()


def install_dist(env):
    # TODO don't rebuild if not changed?
    print("installing...")
    safe_shell_out([env.pip, "install", env.distdir, "--no-clean",
                    "--no-deps", "-t", env.envdistdir],
                   cwd=env.toxdir)


def make_dist(toxinidir, toxdir):
    dist = os.path.join(toxdir, "dist")
    # suppress warnings
    safe_shell_out(["python", "setup.py", "sdist", "--quiet",
                    "--formats=zip", "--dist-dir", dist],
                   cwd=toxinidir)
    v = '-'.join(shell_out(["python", "setup.py", "--name", "--version"],
                           cwd=toxinidir).split())
    return os.path.join(dist, v) + ".zip"


def run_tests(env):
    # Note: it's important all these tests are run, no short-circuiting
    failing = any([run_one_test(env, c[:]) for c in env.commands])
    return failing


def run_one_test(env, command):
    # TODO make sure in env better!!
    # prepend env to first command
    cmd = _cmd = command[0]

    # this is a hack for prettier printing
    if cmd.startswith(env.envbindir):
        _cmd = os.path.relpath(cmd, env.envbindir)
        if _cmd == ".":
            _cmd = cmd
    command[0] = _cmd
    print('(%s) "%s"' % (env.name, ' '.join(command)))
    command[0] = cmd

    if cmd not in env.whitelist and not cmd.startswith(env.envbindir):
        command[0] = os.path.join(env.envbindir, cmd)
    try:
        print(shell_out(command, cwd=env.toxinidir))
        return False
    except OSError as e:
        # TODO question whether command is installed locally?
        cprint("    OSError: %s" % e.args[1], True)
        cprint("    Is %s in your dependancies?\n" % cmd, True)
        return True
    except Exception as e:  # TODO should we captured_output ?
        return True
