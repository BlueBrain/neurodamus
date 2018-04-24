#!/usr/bin/env python
# -*- coding: utf-8 -*-

from neurodamus import Cell
from neurodamus import nrn


def test_create_cell():
    builder = Cell.Builder()
    c = (builder
         .add_root("soma", 1)
         .create_append("dend1", 2, 5)
         .append(builder.Section("dend2", 3, 2)
                 .create_append("sub2_dend", 4, 2))
         .create()
     )
    c.show()
