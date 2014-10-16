"""This module contains the config functions for reading and parsing the
tox.ini file.

Note: Substitutions functions can be found in subst.py.

"""

import re
try:
    from configparser import ConfigParser as SafeConfigParser, NoSectionError, NoOptionError
except ImportError:  # py2, pragma: no cover
    from ConfigParser import SafeConfigParser, NoSectionError, NoOptionError


def read_config(toxinifile):
    config = SafeConfigParser()
    config.read(toxinifile)

    return config


def _get(config, *args):
    try:
        # TODO this could be a while contains braces...?
        # or that could be in replace_braces itself
        return config.get(*args).strip()
    except (NoSectionError, NoOptionError):
        # TODO should this raise??
        return ''


def _get_env_maybe(env, section, option):
    return (_get(env.config, '%s:%s' % (section, env.name), option) or
            _get(env.config, section, option))


def get_whitelist(config):
    return _get(config, 'tox', 'whitelist_externals').split("\n")


def get_changedir(env):
    "changedir = {envdir}"
    from ctox.subst import replace_braces
    changedir = _get_env_maybe(env, 'testenv', 'changedir')
    if changedir:
        return replace_braces(changedir, env)
    else:
        return env.toxinidir


def get_envlist(config):
    from ctox.subst import parse_envlist
    return parse_envlist(_get(config, 'tox', 'envlist'))


def get_deps(env):
    from ctox.subst import replace_braces, expand_factor_conditions
    env_deps = _get_env_maybe(env, "testenv", "deps").strip()

    if env_deps.startswith('-r'):
        requirements_txt = replace_braces(env_deps[2:].strip(), env)
        with open(requirements_txt) as f:
            env_deps = f.read().strip()

    env_deps = [replace_braces(expand_factor_conditions(d, env),
                               env)
                for d in env_deps.split("\n")
                if d]

    env_deps = [d for d in sum((s.split() for s in env_deps), [])
                if not re.match("(pip|conda)([=<>!]|$)", d)]

    return ["pip"] + env_deps


def get_commands(env):
    from ctox.subst import split_on, replace_braces
    # TODO allow for running over new lines? Is this correct at all?
    global_commands = _get(env.config, 'testenv', 'commands')
    env_commands = _get(env.config, 'testenv:%s' % env.name, 'commands')
    commands = (env_commands or global_commands)
    return [split_on(cmd)
            for cmd in split_on(replace_braces(commands, env), '\n')
            if cmd]
