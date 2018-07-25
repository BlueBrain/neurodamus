from __future__ import absolute_import
from neurodamus.lib.configparser import BlueConfig
from os import path

BASEDIR = path.dirname(__file__)


def test_read_config():
    bc = BlueConfig(path.join(BASEDIR, "data"))
    assert len(bc.config) == 4
    assert {"Run", "Stimulus", "StimulusInject", "Report"} <= set(bc.config.keys())
    assert len(bc.config["Stimulus"]) == 2
    assert bc.config["Stimulus"]["poisson1"]["Lambda"] == 20.0
    assert bc.Stimulus["poisson1"]["Lambda"] == 20.0
