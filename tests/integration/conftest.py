import pytest
# !! NOTE: Please don't import NEURON/Neurodamus at module level
# pytest weird discovery system will trigger NEURON init and open a can of worms

# Make all tests run forked
pytestmark = pytest.mark.forked
