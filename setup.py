#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from setuptools import setup

VERSION = "0.4.0"


def setup_package():
    needs_sphinx = {'build_sphinx', 'upload_docs'}.intersection(sys.argv)
    maybe_sphinx = ['sphinx'] if needs_sphinx else []

    setup(
        name='neurodamus',
        version=VERSION,
        packages=[
            "neurodamus",
            "neurodamus.core"
        ],
        install_requires=[
            'NEURON',
            'h5py',
            'enum34;python_version<"3.4"',
            'lazy-property',
            'pyyaml',
            'docopt',
            'six',
        ],
        setup_requires=maybe_sphinx,
        tests_require=[
            "pytest"
        ],
        extras_require={
            'plotting': ['matplotlib'],
            'full': ['matplotlib']
        },
        entry_points={
            'console_scripts': [
                'neurodamus = neurodamus.commands:neurodamus'
            ]
        }
    )


if __name__ == "__main__":
    setup_package()
