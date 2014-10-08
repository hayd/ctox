import os
import re


REPLACEMENTS = {"envpython": "python"}


def bash_expand(s):
    """Usually an envlist is a comma seperated list of pyXX,
    however tox supports move advanced usage, for example:

    >>> s = "{py26,py27}-django{15,16}, py32"
    >>> bash_expand(s)
    ["py26-django15", "py26-django16",
     "py27-django15", "py27-django16", "py32"]
    """
    return sum([_expand_curlys(t) for t in _split_out_of_braces(s)], [])


def parse_tests(env):
    pass


def _replace_curly(envlist, match):
    assert isinstance(envlist, list)
    return [e[:match.start()] + m + e[match.end():]
            for m in re.split("\s*,\s*", match.group()[1:-1])
            for e in envlist]


def parse_envlist(s):
    # TODO some other substitution?
    return bash_expand(s)


def split_on(s, sep=" "):
    """Split s by sep, unless it's inside a quote"""
    pattern = '''((?:[^%s"']|"[^"]*"|'[^']*')+)''' % sep

    return [_strip_speechmarks(t) for t in re.split(pattern, s)[1::2]]


def _strip_speechmarks(t):
    for sm in ["'''", '"""', "'", '"']:
        if t.startswith(sm) and t.endswith(sm):
            return t[len(sm):-len(sm)]
    return t


def _expand_curlys(s):
    """Takes string and returns list of options:

    >>> _expand_curly("py{26, 27}")
    ["py26", "py27"]
    """
    from functools import reduce
    curleys = list(re.finditer("\{[^\{]*\}", s))
    return reduce(_replace_curly, reversed(curleys), [s])


def _split_out_of_braces(s):
    """Generator to split comma seperated string, but not split commas inside
    curly braces.

    >>> list(_split_out_of_braces("py{26, 27}-django{15, 16}, py32"))
    >>>['py{26, 27}-django{15, 16}, py32']
    """
    prev = 0
    for m in re.finditer("\{[^\{]*\}|\s*,\s*", s):
        if not m.group().startswith("{"):
            part = s[prev:m.start()]
            if part:
                yield s[prev:m.start()]
            prev = m.end()
    part = s[prev:]
    if part:
        yield part


def replace_braces(s, config, env):
    def replace(m):
        return _replace_match(m, config, env)
    for _ in range(5):  # depth
        s = re.sub("\{[^\{]*\}", replace, s)
    return s


def _replace_match(m, config, env):
    code = m.group()[1:-1].strip()
    try:
        # TODO could dict values be callable ?
        return REPLACEMENTS[code]
    except KeyError:
        pass

    try:
        return _replace_envvar(code)
    except TypeError:
        pass

    try:
        return _replace_config(code, config, env)
    except TypeError:
        pass

    raise NotImplementedError("{%s} not understood in tox.ini file." % code)


def _replace_envvar(s):
    """{env:KEY} {env:KEY:DEFAULTVALUE}"""
    e = s.split(":")
    if len(e) > 3 or len(e) == 1 or e[0] != "env":
        raise TypeError()
    elif len(e) == 2:
        # Note: this can/should raise a KeyError (according to spec)
        return os.environ[e[1]]
    else:  # len(e) == 3:
        return os.environ.get(e[1], e[2])


def _replace_config(s, config, env):
    "{[sectionname]valuename}"
    m = re.match("\[(.*?)\](.*)", s)
    if m:
        section, option = m.groups()
        expanded = config.get(section, option)
        return '\n'.join([expand_factor_conditions(e, config, env)
                          for e in expanded.split("\n")])
    else:
        raise TypeError()


def expand_factor_conditions(s, config, env):
    "py{33,34}: docformatter"
    e = re.split('\s*\:\s*', s)
    if len(e) == 2 and e[0] != "env":
        env_labels = set(env.split('-'))
        labels = set(bash_expand(e[0]))
        if labels & env_labels:
            return e[1]
        else:
            return ''
    return s
