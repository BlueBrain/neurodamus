#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from setuptools import setup

VERSION = 0.1


def setup_package():
    needs_sphinx = {'build_sphinx', 'upload_docs'}.intersection(sys.argv)
    sphinx = ['sphinx'] if needs_sphinx else []
    setup(
        name='pyNeurodamus',
        version=VERSION,
        setup_requires=['six'] + sphinx,
        install_requires=[
            'NEURON',
            'enum34;python_version<"3.4"',
            'lazy-property', 
            'pyyaml',
            'docopt'
        ],
        entry_points={
            'console_scripts': [
                'neurodamus = neurodamus.commands:neurodamus'
            ]
        }
    )


if __name__ == "__main__":
    setup_package()

