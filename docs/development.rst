How to develop / use a custom Neurodamus-py
===========================================
Neurodamus-py is a Python application. Therefore, all generic procedures on how to manage Python applications generally apply.

Nevertheless, it relies on the availability of some nrnmech libraries for Neuron, which can make the process of running it slightly tricky. Let's therefore describe a bit how it works.

Neurodamus-py package
---------------------
Neurodamus-py is a pure python package, i.e., it doesn't have binary extensions that require some C toolchain to build. As such, you could even potentially just copy the source, and it would be ready to go.

However, that doesn't mean you would be able to run a Neocortex simulation. Please bear in mind an important detail of its design:
 - **Neurodamus-py is completely decoupled from the Neuron model we want to run.**

That means that when launching, you must start it with a "special" binary compiled with nrnivmodl, or neurodamus will attempt loading special's underlying library.

Requirements
------------
Neurodamus-py requires a few dependencies, most of them very usual:

- h5py
- docopt
- libsonata
- psutil

There are also optional dependencies required for some functionalities, so keep them in mind if you are developing:

- scipy
- morphio
- NEURON

Nowadays all these dependencies can be found in PyPI, so it's not a big problem to meet them. Indeed, after a plain "pip install," you can already call the "neurodamus" entry point and inspect the usage.
However, as mentioned, without a compiled model for Neuron, there's nothing much it can do. More on that later.

Install Neurodamus for development
----------------------------------
As with any python package, for development, we recommend installing in dev-mode into a virtualenv:

.. code-block:: bash

    # ensure a recent python is loaded. Consider loading together with dependencies from BB5
    # module load unstable git py-h5py py-libsonata # will also bring Python and mpi

    # Get your copy of neurodamus:
    git clone git@bbpgitlab.epfl.ch:hpc/sim/neurodamus-py.git

    # Create a virtualenv and install in dev-mode (no copies):
    python -m venv venv
    . venv/bin/activate
    pip install -e neurodamus-py

    # Test it
    neurodamus
        Usage:
            neurodamus <BlueConfig> [options]
            neurodamus --help

Perfect, you have neurodamus correctly installed for development.
Let's now try to run some tests.

.. code-block:: bash

    # now, yeah, load a compiled model for Neuron
    module load neurodamus-neocortex
    # Make our neurodamus-py take precedence (see note below)
    export PYTHONPATH=$PWD/neurodamus-py:$PYTHONPATH

    # find the usecase3 simulation in tests
    cd neurodamus-py/tests/simulations/usecase3

    # Run it!
    neurodamus simulation_sonata.json

    # You should get
    # ::INIT:: Special available. Replacing binary...
    # numprocs=1
    # NEURON -- VERSION 9.0.dev-1349-g67a672a2c+ HEAD (67a672a2c+) 2023-05-04
    # ...

    # In order to run on 4 MPI ranks:
    srun -n4 [--account=proj16] neurodamus simulation_sonata.json

That looks good. Notice a couple of things:

If you're a developer, you probably want to start with only one MPI rank. Beware of the size of the simulations, though. You probably want to solve a problem with a minimum reproducer having a couple of cells only.
**"Special available. Replacing binary."** informs us that it detected a "special" binary and is going to use it (instead of attempting to load libnrnmech.so). If you need to disable that, set the env variable: export neurodamus_special=1

.. warning::
    NOTE: Unfortunately, for practical reasons, loading a model like neurodamus-neocortex will add neurodamus-py from the system to PYTHONPATH. While this isn't fully investigated yet, for the moment, we need to override that entry by pushing our own neurodamus-py to the top of PYTHONPATH.

Editing HOC Files
-----------------

When editing the HOC files in ``neurodamus-py/core/hoc``, they will not be picked up automatically. In order for this to work, we need to edit the ``HOC_LIBRARY_PATH`` as follows::

    export HOC_LIBRARY_PATH=${PWD}/core/hoc:${HOC_LIBRARY_PATH}

Running Tests
-------------

Let's run our test suite.

First, we need ``neocortex``::

    module load neurodamus-neocortex

Under ``neurodamus-py``, run ``tox`` with the ``bb5`` environment::

    cd neurodamus-py
    pip install tox
    tox -e bb5

It uses two workers but can still take some time. If you prefer, you can run a single test locally.

Let's experiment with a given scientific test::

    module load neurodamus-neocortex
    pip install pytest pytest-forked
    cd neurodamus-py
    pytest -s -k scientific/test_projections

Prepared Config Files
---------------------

The following repository contains the required input files for a number of simulations::

    git clone git@bbpgitlab.epfl.ch:hpc/sim/blueconfigs.git

The quick path way
------------------

Very often we want to reproduce the setup from BB5 to work on top of it, to ensure the stack is 100% the same.

For that, consider doing::

    # Load the setup (change neurodamus-neocortex with that interesting for you)
    module load unstable py-neurodamus neurodamus-neocortex

    # Set up a virtualenv for other packages, e.g. pytest
    # Remember that any installed package in this venv takes precedence over the loaded module
    python -m venv venv
    . venv/bin/activate
    pip install pytest pytest-forked

    # Make dev neurodamus-py take precedence over everything
    export PYTHONPATH=$PWD/neurodamus-py:$PYTHONPATH

    # You should be good to go
    cd neurodamus-py
    pytest -s -k scientific/test_projections

Installing With Spack
---------------------

The alternative to using pip is to use Spack. First ensure that you've got modifiable version of spack, e.g.::

    module load unstable spack
    # and follow the instructions provided to get an editable version.

Next, create a Spack environment and add the desired packages::

    spack env create neurodamus
    spack env activate -p neurodamus

    spack add neurodamus-neocortex

You can clone ``neurodamus-py`` and use ``spack develop`` as follows::

    git clone git@bbpgitlab.epfl.ch:hpc/sim/neurodamus-py.git
    spack develop -p ${PWD}/neurodamus-py --no-clone py-neurodamus@develop
    spack add py-neurodamus@develop

    spack install --jobs NPROC

.. note::

    Remember, there's a Spack gotcha that the first time one activates a freshly created environment it'll usually not configure the environment correctly. Inparticular, neither PYTHONPATH  nor HOC_LIBRARY_PATH  will be set to the appropriate values. Therefore, perform a:

    .. code-block:: bash

        spack env deactivate
        spack env activate -p neurodamus
        # This tends to manifest itself in import errors: ModuleNotFoundError: No module named 'neurodamus'.

.. note::

    The recipe for neurodamus-neocortex  will install the HOC files in core/hoc  from neurodamus-py as symbolic links. This means that existing HOC files in core/hoc  can be edited, but new files wont be visible without performing a:

    .. code-block:: bash

        spack uninstall neurodamus-neocortex
        spack install neurodamus-neocortex
        # This is required since changing the sources in neurodamus-py doesn't trigger Spack to reinstall neurodamus-neocortex.

.. note::

    It is not possible to use spack develop  for neurodamus-model  or neurodamus-neocortex (and others). Instead it's important to always install them by downloading the sources from Gitlab. If one must edit those sources, the recommended workflow is to create a feature branch in the respective repository and convince Spack to use that branch.

.. note::

    It's likely best to not mix this with the regular modules for anything neurodamus related. It's also not required since, anything that's available can also be found and reused by regular Spack. Hence, any packages that have already been installed and would be available via module load  would not be recompiled.
