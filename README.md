ctox
====

[tox](http://tox.readthedocs.org/) but with conda.

This is a really rough hack to replicate tox using conda, you'll be much
better off using tox.

Currently:

- does no caching of builds
- no cli options
- no parallel support (see above)
- even in this minimal implementation: bugs
- it's just a bit of fun

The neat thing is that it makes tox-like testing on a machine with conda
installed but not all python versions (e.g. no python 3). In theory it might
also be useful for the scientific python stack if builds were cached, at the
moment they're not.

In conclusion, don't use this, here be :dragon:s.

---

Usage:

In the project's directory (which has the appropriate `tox.ini`):

```sh
cd project_dir
ctox
```
