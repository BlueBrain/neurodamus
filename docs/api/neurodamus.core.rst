=======================
neurodamus.core package
=======================


.. automodule:: neurodamus.core
   :members:
   :undoc-members:

   .. rubric:: Classes

   .. autosummary::
      Neuron
      MPI
      NeurodamusCore
      Cell
      CurrentSource
      ProgressBarRank0

   .. rubric:: Decorators

   .. autosummary::
      return_neuron_timings
      mpi_no_errors
      run_only_rank0


Sub-Modules
===========

.. autosummary::
   cell
   configuration
   mechanisms
   random
   stimuli
   synapses


Module API
==========

.. autoclass:: Neuron
   :members:

.. autoclass:: MPI

   *property* :py:attr:`rank` The id of the current MPI rank

   *property* :py:attr:`size` The number of MPI ranks

.. autoclass:: NeurodamusCore
   :members:

.. autoclass:: Cell
   :members:

.. autoclass:: CurrentSource
   :members:

.. autoclass:: ProgressBarRank0
   :members:

.. autoclass:: neurodamus.core._neuron._Neuron
   :members: h, load_dll, load_hoc, require, run_sim, section_in_stack


**Decorators**

.. autofunction:: return_neuron_timings

.. autofunction:: mpi_no_errors

.. autofunction:: run_only_rank0
