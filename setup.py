#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import sys
from setuptools import setup, find_packages

try:
    v = subprocess.run(['git', 'describe', '--tags'],
                       stdout=subprocess.PIPE).stdout.strip().decode()
    __version__ = v[: v.rfind("-")].replace("-", ".dev") if "-" in v else v
except Exception as e:
    raise RuntimeError("Could not get version from Git repo") from e


package_info = dict(
    name='neurodamus-py',
    version=__version__,
    packages=find_packages(exclude=["tests"]),
    install_requires=[
        'h5py',
        'docopt',
        'libsonata',
        'psutil',
    ],
    setup_requires=(["pytest-runner"] if "test" in sys.argv else []),
    tests_require=["pytest"],
    extras_require=dict(
        plotting=['matplotlib'],   # only for Neurodamus HL API
        full=['scipy', 'morphio', 'NEURON', 'mvdtool'],
    ),
    entry_points=dict(
        console_scripts=[
            'neurodamus = neurodamus.commands:neurodamus',
            'hocify = neurodamus.commands:hocify',
        ]
    ),
)


if __name__ == "__main__":
    setup(**package_info)
