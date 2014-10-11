ctox
====

[tox](http://tox.readthedocs.org/) but with conda.

[![Build Status](https://travis-ci.org/hayd/ctox.svg?branch=master)](https://travis-ci.org/hayd/ctox)

This is a really rough hack to replicate tox using conda (Note that tox is
*professionally supported* whilst ctox isn't supported). In the long-term a
much better solution is to add conda support to tox...

Currently:

- conda envs and dependancies are cached (very naively)
- some tox substitutions (some missing features)
- ~~no~~ some cli options (lots of missing features)
- no parallel support (yet)
- bugs (probably lots)

However, the neat thing is that it makes tox-like testing on a machine with
conda installed, but not all python versions are installed.

In conclusion, you're probably better off using tox, here be :dragon:s.

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
# or to pdb into any failing environments
ctox -- --pdb --pdb-fail
```
*Note this assumes you have something like `nosetest {posargs}` (or
`py.test {posargs}`) in the projects tox.ini file. which this will be replaced
with `nosetest --pdb --pdb-fail` (or `py.test --pdb --pdb-fail`).*


Why
---
I was sick of `InterpreterNotFound` when trying to use tox having installed
python with conda. This solves that and I thought it wouldn't take
very long to put together. No doubt I should've just hacked on tox, which in
the long-run will be the best solution, but there you are!