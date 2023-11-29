import os
import pytest

assert os.environ.get("NEURODAMUS_NEOCORTEX_ROOT"), \
    "Test requires loading a neocortex model to run"
assert os.path.isfile("/gpfs/bbp.cscs.ch/project/proj83/circuits/Bio_M/20200805/circuit.mvd3"), \
    "Circuit file not available"

pytestmark = [
    pytest.mark.forked,
]
