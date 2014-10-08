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
    sub = kwargs.pop("sub", False)
    if sub:
        raise TypeError("Unknown kwarg passed.")
    try:
        return config.get(*args)
    except (NoSectionError, NoOptionError):
        return ''


def get_whitelist(config):
    return _get(config, 'tox', 'whitelist_externals').split("\n")

def get_envlist(config):
    from ctox.subst import parse_envlist
    return parse_envlist(_get(config, 'tox', 'envlist'))


def get_deps(env, config, sub=False):
    deps = _get(config, 'testenv', 'deps').split()
    env_deps = _get(config, 'testenv:%s' % env, 'deps').split()
    return [d for d in ["pip"] + deps + env_deps
            if not re.match("conda([=<>!]|$)", d)]

def get_commands(env, config):
    from ctox.subst import replace_braces, split_on
    # TODO allow for running over new lines? Is this correct at all?
    commands = _get(config, 'testenv', 'commands').split("\n")
    env_commands = _get(config, 'testenv:%s' % env, 'commands').split("\n")
    res= [split_on(replace_braces(cmd)) for cmd in commands + env_commands if cmd]
    return res
