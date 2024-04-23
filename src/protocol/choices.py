import sys
from enum import Enum
from typing import Literal

from .common import Parser
from .parser_300 import Parser300
from .parser_re import ParserRE

if sys.version_info[1] >= 10:
    from .parser_310 import Parser310
    from .parser_3102 import Parser3102

    def __default_parser() -> type[Parser]:
        return Parser310

    def __parser_310() -> type[Parser]:
        return Parser310

    def __parser_3102() -> type[Parser]:
        return Parser3102

else:

    def __default_parser() -> type[Parser]:
        return Parser300

    def __parser_310() -> type[Parser]:
        raise ValueError("PARSER_310 is not supported on Python < 3.10")

    def __parser_3102() -> type[Parser]:
        raise ValueError("PARSER_3102 is not supported on Python < 3.10")


class Backend(str, Enum):
    PARSER_300 = "300"
    PARSER_310 = "310"
    PARSER_3102 = "3102"
    PARSER_RE = "re"
    DEFAULT = "default"


def make_parser(
    backend: Backend | Literal["300", "310", "3102", "re", "default"] = Backend.DEFAULT,
) -> Parser:
    parser_type: type[Parser]
    if backend == Backend.DEFAULT:
        parser_type = __default_parser()
    elif backend == Backend.PARSER_300:
        parser_type = Parser300
    elif backend == Backend.PARSER_310:
        parser_type = __parser_310()
    elif backend == Backend.PARSER_3102:
        parser_type = __parser_3102()
    elif backend == Backend.PARSER_RE:
        parser_type = ParserRE
    else:
        raise ValueError(f"Unknown parser implementation: {backend}")
    return parser_type()
