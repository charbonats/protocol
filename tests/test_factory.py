from __future__ import annotations

import sys

import pytest
from protocol import Backend, make_parser
from protocol.common import Parser


def test_make_parser_default() -> None:
    parser = make_parser()
    assert type(parser).__name__ == "Parser300"


def test_make_parser_300() -> None:
    parser: Parser = make_parser(Backend.PARSER_300)
    assert type(parser).__name__ == "Parser300"


def test_make_parser_310() -> None:
    if sys.version_info < (3, 10):
        with pytest.raises(ValueError) as exc:
            make_parser(Backend.PARSER_310)
        assert exc.match("Python 3.10 or later is required")
        return
    parser = make_parser(Backend.PARSER_310)
    assert parser is not None
    assert type(parser).__name__ == "Parser310"


def test_make_parser_re() -> None:
    parser = make_parser(Backend.PARSER_RE)
    assert parser is not None
    assert type(parser).__name__ == "ParserRE"


def test_make_parser_invalid() -> None:
    with pytest.raises(ValueError) as exc:
        make_parser("invalid")  # type: ignore
    assert exc.match("unknown parser implementation: invalid")
