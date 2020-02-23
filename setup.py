#! /usr/bin/env python
# -*- coding:utf-8 -*-
""" IoT-Lab Install library setuptools script. Use mainly for testing """
import sys

from setuptools import setup, find_packages


PACKAGE = 'fabdockerfile'
VERSION = '0.1'
PY3_OR_LATER = sys.version_info[0] >= 3

DESCRIPTION = """
"""

setup(
    name=PACKAGE,
    version=VERSION,
    description='Fabric-Dockerfile, run a Fabric task and generate a Dockerfile'
    ' that ',
    author='Matthieu Berthomé',
    author_email='rienafairefr@gmail.com',
    download_url='http://github.com/rienafairefr/fabric-dockerfile',
    packages=find_packages(),
    classifiers=['Programming Language :: Python',
                 'Programming Language :: Python :: 2',
                 'Topic :: Utilities', ],
    install_requires=['fabric3>=1.10' if PY3_OR_LATER
                      else 'fabric<2.0.0', 'docker-map', 'docker-py',
                      'configobj', 'pexpect', 'jinja2']
)
