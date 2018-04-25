from __future__ import print_function
from os import path
from neurodamus import Cell

d = path.dirname(__file__)
c = Cell(1, path.join(d, "morphology/C060114A7.asc"))
print("Len:", len(c.all))
print(c.axons[4])
