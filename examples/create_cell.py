#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A few ways to create a cell with two branches, one of then two sections long"""
from neurodamus import Cell


def test_create_cell():
    builder = Cell.Builder
    c = (builder
         .add_soma(1)
         .add("dend1", 2, 5)
         .attach(builder.Section("dend2", 3, 2).add("sub2_dend", 4, 2))
         .create())


def test_create_cell_2():
    c = (Cell.Builder
         .add_soma(1)
         .add("dend1", 2, 5)
         .append("dend2", 3, 2).add("sub2_dend", 4, 2)
         .create())


def test_create_cell_3():
    Sec = Cell.Builder.Section
    c = (Cell.Builder
         .add_soma(1)
         .add("dend1", 2, 5)
         .attach(Sec("dend2", 3, 2)
                 .append("sub2_dend", 4, 2)
                 .get_root())
         .create())


if __name__ == "__main__":
    test_create_cell()
    test_create_cell_2()
    test_create_cell_3()
    Cell.show_topology()
