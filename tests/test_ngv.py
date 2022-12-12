"""
Test suite for Neurodamus NGV support
"""
import os
import os.path as osp
import pytest


@pytest.mark.slow
@pytest.mark.forked
@pytest.mark.skipif(
    not os.environ.get("NEURODAMUS_NEOCORTEX_ROOT"),
    reason="Test requires loading a neocortex model to run")
def test_loading_and_run():
    """Base testing: we instantiate neurodamus and run a simple simulation with ngv stuff"""
    from neurodamus import Neurodamus
    blueconfig = osp.join(osp.abspath(osp.dirname(__file__)),
                          "simulations", "ngv", "BlueConfig")
    ndam = Neurodamus(blueconfig, logging_level=2)
    ndam.solve(2)

if __name__ == "__main__":
    test_loading_and_run()