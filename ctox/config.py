import os
import re
try:
    from configparser import ConfigParser as SafeConfigParser, NoSectionError, NoOptionError
except ImportError:  # py2, pragma: no cover
    from ConfigParser import SafeConfigParser, NoSectionError, NoOptionError


def read_config(cwd):
    tox_file = os.path.join(cwd, 'tox.ini')

    config = SafeConfigParser()
    config.read(tox_file)

    return config


def _get(config, *args, **kwargs):
    if kwargs:
        raise TypeError("Unknown kwarg passed.")
    try:
        # TODO this could be a while contains braces...?
        # or that could be in replace_braces itself
        return config.get(*args)
    except (NoSectionError, NoOptionError):
        # TODO should this raise??
        return ''


def get_whitelist(config):
    return _get(config, 'tox', 'whitelist_externals').split("\n")


def get_envlist(config):
    from ctox.subst import parse_envlist
    return parse_envlist(_get(config, 'tox', 'envlist'))


def get_deps(env, config, sub=False):
    from ctox.subst import replace_braces, expand_factor_conditions
    env_deps = (_get(config, 'testenv:%s' % env, 'deps') or
                _get(config, 'testenv', 'deps'))

    env_deps = [replace_braces(expand_factor_conditions(d, config, env),
                               config, env)
                for d in env_deps.split("\n")
                if d]

    env_deps = [d for d in sum((s.split() for s in env_deps), [])
                if not re.match("(pip|conda)([=<>!]|$)", d)]

    return ["pip"] + env_deps


def get_commands(env, config):
    from ctox.subst import split_on, replace_braces
    # TODO allow for running over new lines? Is this correct at all?
    global_commands = _get(config, 'testenv', 'commands')
    env_commands = _get(config, 'testenv:%s' % env, 'commands')
    commands = (env_commands or global_commands)
    return [split_on(cmd)
            for cmd in split_on(replace_braces(commands, config, env), '\n')
            if cmd]
