"""
ConfigParser module
-------------------
A module which parses the BlueConfig master file.

Copyright 2018 - Blue Brain Project, EPFL
"""
from __future__ import absolute_import
from os import path
import yaml


class BlueConfig:
    """
    BlueConfig parser. The syntax shall be javascript compatible, i.e. string values shall be
    always quoted, and fields separated by comma. Keys can be provided as direct text.
    E.g.
    Stimulus:
      poisson1:
        Mode:       Current
        Pattern:    NPoisson
        AmpStart:   0.000000
        Lambda:     20.000000
    """
    def __init__(self, filepath):
        if path.isdir(filepath):
            filepath = path.join(filepath, "BlueConfig.yaml")
        self.config = yaml.load(open(filepath))

    @property
    def Run(self):
        return self.config["Run"]

    @property
    def Stimulus(self):
        return self.config["Stimulus"]

    @property
    def StimulusInject(self):
        return self.config["StimulusInject"]

    @property
    def Reports(self):
        return self.config["Report"]
