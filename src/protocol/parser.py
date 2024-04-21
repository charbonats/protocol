"""protocol.parser module."""

from enum import IntEnum, auto


class State(IntEnum):
  OP_START = 0
  OP_PLUS = auto()
  OP_PLUS_O = auto()
  OP_PLUS_OK = auto()
  OP_MINUS = auto()
  OP_MINUS_E = auto()
  OP_MINUS_ER = auto()
  OP_MINUS_ERR = auto()
  OP_MINUS_ERR_SPC = auto()
  MINUS_ERR_ARG = auto()
  OP_M = auto()
  OP_MS = auto()
  OP_MSG = auto()
  OP_MSG_SPC = auto()
  MSG_ARG = auto()
  MSG_PAYLOAD = auto()
  MSG_END = auto()
  OP_H = auto()
  OP_P = auto()
  OP_PI = auto()
  OP_PIN = auto()
  OP_PING = auto()
  OP_PO = auto()
  OP_PON = auto()
  OP_PONG = auto()
  OP_I = auto()
  OP_IN = auto()
  OP_INF = auto()
  OP_INFO = auto()
  OP_INFO_SPC = auto()
  INFO_ARG = auto()



class Parser:
    """NATS Protocol parser."""

    def __init__(self) -> None:
       self.state = State.OP_START

    def parse(self, data: bytes) -> None:
       """Parse some bytes."""
