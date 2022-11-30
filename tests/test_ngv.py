"""
Test suite for Neurodamus NGV support
"""
import os.path as osp

def test_loading_and_run():
    """Base testing: we instantiate neurodamus and run a simple simulation with ngv stuff"""
    from neurodamus import Neurodamus
    blueconfig = osp.join(osp.abspath(osp.dirname(__file__)),
                          "simulations", "ngv", "BlueConfig")
    ndam = Neurodamus(blueconfig, logging_level=2)
    ndam.run()

if __name__ == "__main__":
    test_loading_and_run()