from __future__ import annotations

import sys
from enum import Enum
from typing import Literal

from .common import Parser
from .parser_300 import Parser300
from .parser_re import ParserRE


def __default_parser() -> type[Parser]:
    return Parser300


if sys.version_info[1] >= 10:
    from .parser_310 import Parser310

    def __parser_310() -> type[Parser]:
        return Parser310


else:

    def __parser_310() -> type[Parser]:
        raise RuntimeError("python 3.10 or later is required")


class Backend(str, Enum):
    PARSER_300 = "300"
    PARSER_310 = "310"
    PARSER_RE = "re"


def make_parser(
    backend: Backend | Literal["300", "310", "re"] | None = None,
) -> Parser:
    parser_type: type[Parser]
    if backend is None:
        parser_type = __default_parser()
    elif backend == Backend.PARSER_300:
        parser_type = Parser300
    elif backend == Backend.PARSER_310:
        parser_type = __parser_310()
    elif backend == Backend.PARSER_RE:
        parser_type = ParserRE
    else:
        raise ValueError(f"unknown parser implementation: {backend}")
    return parser_type()
