from enum import Enum


class Mode(Enum):
    SINK = 1
    WRAPPER = 2
    PIPE_IN = 3
    PIPE_OUT = 4
    PIPE_BOTH = 5
