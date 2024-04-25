from __future__ import annotations

import pytest
from protocol import Backend, make_parser
from protocol.parser_300 import Parser300
from protocol.parser_310 import Parser310
from protocol.parser_re import ParserRE


def test_make_parser_default() -> None:
    parser = make_parser()
    assert isinstance(parser, Parser300)


def test_make_parser_300() -> None:
    parser = make_parser(Backend.PARSER_300)
    assert isinstance(parser, Parser300)


def test_make_parser_310() -> None:
    parser = make_parser(Backend.PARSER_310)
    assert parser is not None
    assert isinstance(parser, Parser310)


def test_make_parser_re() -> None:
    parser = make_parser(Backend.PARSER_RE)
    assert parser is not None
    assert isinstance(parser, ParserRE)


def test_make_parser_invalid() -> None:
    with pytest.raises(ValueError) as exc:
        make_parser("invalid")  # type: ignore
    assert exc.match("unknown parser implementation: invalid")
