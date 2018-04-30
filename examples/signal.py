#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
from neurodamus import StimuliSource

s = StimuliSource.train(0.5, 100, 4, 100)
s.add_noise(0, 0.1, 100)
ax = s.plot(ylims=(-1, 1))
