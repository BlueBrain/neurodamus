from setuptools import setup, find_packages


setup(
    name='neurodamus',
    author='Blue Brain Project, EPFL',
    packages=find_packages(exclude=["tests"]),
    install_requires=[
        'h5py',
        'docopt',
        'libsonata',
        'psutil',
        'setuptools',
    ],
    setup_requires=["setuptools_scm"],
    use_scm_version={"local_scheme": "no-local-version"},
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
