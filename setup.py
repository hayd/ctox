#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ast import parse
import os
from setuptools import setup
from sys import version_info


def version():
    """Return version string."""
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)),
                           'ctox',
                           'main.py')) as input_file:
        for line in input_file:
            if line.startswith('__version__'):
                return parse(line).body[0].value.s


def readme():
    try:
        import pypandoc
        return pypandoc.convert('README.md', 'rst', format='md')
    except (IOError, ImportError):
        with open('README.md') as f:
            return f.read()

INSTALL_REQUIRES = (
    ['colorama'] +
    (['argparse'] if version_info < (2, 7) else []) +
    ['pip']
)

setup(
    name='ctox',
    version=version(),
    description="tox but with conda",
    long_description=readme(),
    license='MIT License',
    author='Andy Hayden',
    author_email='andyhayden1@gmail.com',
    url='https://github.com/hayd/ctox',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing',
    ],
    keywords='conda, tox, testing, virtualenv',
    install_requires=INSTALL_REQUIRES,
    packages=['ctox'],
    test_suite='tests',
    zip_safe=False,
    entry_points={'console_scripts': ['ctox = ctox.main:_main',
                                      'ctox_ = ctox.main:_main']},
)
