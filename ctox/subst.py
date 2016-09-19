"""This module contains functions to deal with substitution of tox.ini config
files.

The most useful are bash_expand and replace_braces.

"""
import os
import re


DEPTH = 5


def parse_commands(env):
    pass


def parse_envlist(s):
    """Expand the tox.ini's envlist into a fully expanded list.

    Example
    -------
    >>> s = "{py26,py27}-django{15,16}, py32"
    >>> parse_envlist(s)
    ["py26-django15", "py26-django16", "py27-django15", "py27-django16",
    "py32"]

    """
    # TODO some other substitutions?
    return bash_expand(s)


def expand_curlys(s):
    """Takes string and returns list of options:

    Example
    -------
    >>> expand_curlys("py{26, 27}")
    ["py26", "py27"]

    """
    from functools import reduce
    curleys = list(re.finditer(r"{[^{}]*}", s))
    return reduce(_replace_curly, reversed(curleys), [s])


def _replace_curly(envlist, match):
    assert isinstance(envlist, list)
    return [e[:match.start()] + m + e[match.end():]
            for m in re.split(r"\s*,\s*", match.group()[1:-1])
            for e in envlist]


def bash_expand(s):
    """Usually an envlist is a comma seperated list of pyXX, however tox
    supports move advanced usage.

    Example
    -------
    >>> s = "{py26,py27}-django{15,16}, py32"
    >>> bash_expand(s)
    ["py26-django15", "py26-django16", "py27-django15", "py27-django16",
    "py32"]

    """
    return sum([expand_curlys(t) for t in _split_out_of_braces(s)], [])


def _split_out_of_braces(s):
    """Generator to split comma seperated string, but not split commas inside
    curly braces.

    >>> list(_split_out_of_braces("py{26, 27}-django{15, 16}, py32"))
    >>>['py{26, 27}-django{15, 16}, py32']

    """
    prev = 0
    for m in re.finditer(r"{[^{}]*}|\s*,\s*", s):
        if not m.group().startswith("{"):
            part = s[prev:m.start()]
            if part:
                yield s[prev:m.start()]
            prev = m.end()
    part = s[prev:]
    if part:
        yield part


def expand_factor_conditions(s, env):
    """If env matches the expanded factor then return value else return ''.

    Example
    -------
    >>> s = 'py{33,34}: docformatter'
    >>> expand_factor_conditions(s, Env(name="py34", ...))
    "docformatter"
    >>> expand_factor_conditions(s, Env(name="py26", ...))
    ""

    """
    try:
        factor, value = re.split(r'\s*\:\s*', s)
    except ValueError:
        return s

    if matches_factor_conditions(factor, env):
        return value
    else:
        return ''


def matches_factor_conditions(s, env):
    """"Returns True if py{33, 34} expanded is contained in env.name."""
    env_labels = set(env.name.split('-'))
    labels = set(bash_expand(s))
    return bool(labels & env_labels)


def split_on(s, sep=" "):
    """Split s by sep, unless it's inside a quote."""
    pattern = '''((?:[^%s"']|"[^"]*"|'[^']*')+)''' % sep

    return [_strip_speechmarks(t) for t in re.split(pattern, s)[1::2]]


def _strip_speechmarks(t):
    for sm in ["'''", '"""', "'", '"']:
        if t.startswith(sm) and t.endswith(sm):
            return t[len(sm):-len(sm)]
    return t


def replace_braces(s, env):
    """Makes tox substitutions to s, with respect to environment env.

    Example
    -------
    >>> replace_braces("echo {posargs:{env:USER:} passed no posargs}")
    "echo andy passed no posargs"

    Note: first "{env:USER:}" is replaced with os.environ.get("USER", ""),
    the "{posargs:andy}" is replaced with "andy" (since no posargs were
    passed).

    """
    def replace(m):
        return _replace_match(m, env)
    for _ in range(DEPTH):
        s = re.sub(r"{[^{}]*}", replace, s)
    return s


def _replace_match(m, env):
    """Given a match object, having matched something inside curly braces,
    replace the contents if matches one of the supported tox-substitutions."""
    # ditch the curly braces
    s = m.group()[1:-1].strip()

    try:
        # get the env attributes e.g. envpython or toxinidir.
        # Note: if you ask for a env methodname this will raise
        # later on... so don't do that.
        return getattr(env, s)
    except AttributeError:
        pass

    for r in [_replace_envvar, _replace_config, _replace_posargs]:
        try:
            return r(s, env)
        except ValueError:
            pass

    raise NotImplementedError("{%s} not understood in tox.ini file." % s)


def _replace_envvar(s, _):
    """env:KEY or env:KEY:DEFAULT"""
    e = s.split(":")
    if len(e) > 3 or len(e) == 1 or e[0] != "env":
        raise ValueError()
    elif len(e) == 2:
        # Note: this can/should raise a KeyError (according to spec).
        return os.environ[e[1]]
    else:  # len(e) == 3
        return os.environ.get(e[1], e[2])


def _replace_config(s, env):
    """[sectionname]optionname"""
    m = re.match(r"\[(.*?)\](.*)", s)
    if m:
        section, option = m.groups()
        expanded = env.config.get(section, option)
        return '\n'.join([expand_factor_conditions(e, env)
                          for e in expanded.split("\n")])
    else:
        raise ValueError()


def _replace_posargs(s, env):
    "posargs:DEFAULT"
    e = re.split(r'\s*\:\s*', s)
    if e and e[0] == "posargs":
        from ctox.main import positional_args
        return (" ".join(positional_args(env.options)) or
                (e[1] if len(e) > 1 else ""))
    else:
        raise ValueError()
