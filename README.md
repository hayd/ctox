ctox
====

[tox](http://tox.readthedocs.org/) but with conda.

[![Build Status](https://travis-ci.org/hayd/ctox.svg?branch=master)](https://travis-ci.org/hayd/ctox)

This is a really rough hack to replicate tox using conda, you'll be much
better off using tox (tox is *professionally supported* whilst ctox isn't
supported). In the long-term a much better solution is to add conda support
to tox...

Currently:

- conda envs and dependancies are cached (naively)
- some tox substitutions (lots of missing features)
- no cli options
- no parallel support (see above)
- bugs (probably lots)

However, the  neat thing is that it makes tox-like testing on a machine with
conda installed but not all python versions (e.g. no native python 3).
Potentially this might also be useful for the scientific python stack...

In conclusion, don't use this, here be :dragon:s.

Usage
-----

Have conda installed on your system. The recommended way (I think) is via
[miniconda](http://conda.pydata.org/miniconda.html), the not recommended
way (which will almost certainly fail) is via pip, please don't use this
with conda installed via pip.

In the project's directory (which has a `tox.ini` file):

```sh
cd project_dir
ctox
```

Why
---
I was sick of `InterpreterNotFound` when trying to use tox having installed
python with conda. This solves that neatly and I thought it wouldn't take
very long to put together. No doubt I should've just hacked on tox, but
there you are!

Why not?