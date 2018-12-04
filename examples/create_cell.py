#!/usr/bin/env python
"""
A few ways to create a cell with two branches, one of then two sections long
"""
from neurodamus.core import Cell


def test_create_cell():
    builder = Cell.Builder
    c = (builder
         .add_soma(1)
         .add_dendrite("dend1", 2, 5)
         .attach(builder.DendriteSection("dend2", 3, 2).add("sub2_dend", 4, 2))
         .create())
    return c


def test_create_cell_2():
    c = (Cell.Builder
         .add_soma(1)
         .add_dendrite("dend1", 2, 5)
         # Three axon sections in line
         .append_axon("ax1", 3, 2).append("ax1_2", 4, 2).append("ax1_3", 3, 3)
         .create())
    return c


def test_create_cell_3():
    Dend = Cell.Builder.DendriteSection
    c = (Cell.Builder
         .add_soma(1)
         .add_dendrite("dend1", 2, 5)
         .attach(Dend("dend2", 3, 2)
                 .append("sub2_dend", 4, 2)
                 .get_root())
         .create())
    return c


if __name__ == "__main__":
    test_create_cell()
    test_create_cell_2()
    test_create_cell_3()
    Cell.show_topology()
