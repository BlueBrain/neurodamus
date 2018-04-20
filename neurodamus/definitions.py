from enum import Enum


class TType(Enum):
    NUMBER = 0
    OBJREF = 1
    STRDEF = 2
    POINTER = 3
    NOTEXIST = -1
