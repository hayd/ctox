import os

from ctox.shell import safe_shell_out, CalledProcessError, shell_out, cprint


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
                               "--yes", "--quiet"]))
    return success


def create_env(env, cwd, force_remove=False):
    py_version = '.'.join(env[2:4])
    # TODO cache cache cache!

    if force_remove:
        shell_out(['conda', 'remove', '-p', env, '--all',
                   '--yes', '--quiet'],
                  cwd=cwd)

    shell_out(['conda', 'create', '-p', env,
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
        # Note: deps
        success = all(uninstall(d, env=env, cwd=cwd) for d in deps[1:])
        if (not success) or deps[0] != "pip":
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


def install_dist(env, cwd, dist):
    # TODO don't rebuild if not changed?
    print("installing...")
    pip = os.path.join(cwd, env, "bin", "pip")
    local_dist = os.path.join(cwd, env, "dist")
    safe_shell_out([pip, "install", dist, "--no-clean", "--no-deps", "-t", local_dist],
                   cwd=cwd)


def make_dist(parent, cwd):
    dist = os.path.join(cwd, "dist")
    # suppress warnings
    safe_shell_out(["python", "setup.py", "sdist", "--quiet",
                    "--formats=zip", "--dist-dir", dist],
                   cwd=parent)
    v = '-'.join(shell_out(["python", "setup.py", "--name", "--version"],
                           cwd=parent).split())
    return os.path.join(dist, v) + ".zip"


def run_tests(env, commands, cwd, parent, whitelist):
    # Note: it's important all these tests are run, no short-circuiting
    failing = any([run_one_test(env, c[:], cwd, parent, whitelist)
                   for c in commands])
    return failing


def run_one_test(env, command, cwd, parent, whitelist):
    # TODO make sure in env better!!
    # prepend env to first command
    print('(%s) "%s"' % (env, ' '.join(command)))
    cmd = command[0]
    if cmd not in whitelist:
        command[0] = os.path.join(cwd, env, 'bin', cmd)
    try:
        print(shell_out(command, cwd=parent))
        return False
    except OSError as e:
        # TODO question whether command is installed locally?
        cprint("    OSError: %s" % e.args[1], True)
        cprint("    Is %s in your dependancies?\n" % cmd, True)
        return True
    except Exception as e:  # TODO should we captured_output ?
        return True
