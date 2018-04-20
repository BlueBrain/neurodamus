#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from setuptools import setup

VERSION = 0.1


def setup_package():
    needs_sphinx = {'build_sphinx', 'upload_docs'}.intersection(sys.argv)
    sphinx = ['sphinx'] if needs_sphinx else []
    setup(
        name="pyNeurodamus",
        version=VERSION,
        setup_requires=['six'] + sphinx,
        install_requires=['NEURON', "lazy-property"]
    )


if __name__ == "__main__":
    setup_package()
