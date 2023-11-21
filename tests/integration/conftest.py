import pytest
# !! NOTE: Please don't import neron/neurodamus at module level
# pytest weird discovery system will trigger Neuron init and open can of worms

# Make all tests run forked
pytestmark = pytest.mark.forked
