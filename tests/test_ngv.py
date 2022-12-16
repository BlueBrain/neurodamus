"""
Test suite for Neurodamus NGV support
"""
import os.path as osp


if __name__ == "__main__":
    from neurodamus import Neurodamus
    blueconfig = osp.join(osp.abspath(osp.dirname(__file__)),
                          "simulations", "ngv", "BlueConfig")
    Neurodamus(blueconfig, logging_level=2).run()
