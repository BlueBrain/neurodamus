#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A few ways to create a cell with two branches, one of then two sections long"""
from neurodamus import Cell


def test_create_cell():
    builder = Cell.Builder
    c = (builder
         .add_root("soma", 1)
         .add("dend1", 2, 5)
         .attach(builder.Section("dend2", 3, 2)
                 .add("sub2_dend", 4, 2))
         .create())
    Cell.show_topology()


def test_create_cell_2():
    c = (Cell.Builder
         .add_root("soma", 1)
         .add("dend1", 2, 5)
         .append("dend2", 3, 2).add("sub2_dend", 4, 2)
         .create()
     )
    Cell.show_topology()


def test_create_cell_3():
    SB = Cell.Builder.Section
    c = (Cell.Builder
         .add_root("soma", 1)
         .add("dend1", 2, 5)
         .attach(SB("dend2", 3, 2)
                 .append("sub2_dend", 4, 2)
                 .get_root())
         .create()
     )
    Cell.show_topology()


if __name__ == "__main__":
    print("#1 ------------------------")
    test_create_cell()
    print("#2 ------------------------")
    test_create_cell_2()
    print("#3 ------------------------")
    test_create_cell_3()
