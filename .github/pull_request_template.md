## Context
<!-- Please brifly describe the problem the PR solves and what the solution was -->

## Scope
<!--
Please describe in more detail the several changes implemented. How did we solve it?
E.g. change component-A to..., created a new data structure, etc...
-->

## Testing
<!--
Please add a new test under `tests`. Consider the following cases:

 1. If the change is in an independent component (e.g, a new container type, a parser, etc) a bare unit test should be sufficient. See e.g. `tests/test_coords.py`
 2. If you are fixing or adding components supporting a scientific use case, affecting node or synapse creation, etc..., which typically rely on Neuron, tests should set up a simulation using that feature, instantiate neurodamus, **assess the state**, run the simulation and check the results are as expected.
    See an example at `tests/test_simulation.py#L66`
-->

## Review
* [ ] PR description is complete
* [ ] Coding style (imports, function length, New functions, classes or files) are good
* [ ] Unit/Scientific test added
* [ ] Updated Readme, in-code, developer documentation
