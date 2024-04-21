import itertools

import pytest
from protocol.parser import ErrorEvent, Event, Operation, Parser, State


def parse_text(data: str) -> tuple[list[State], list[Event]]:
    parser = Parser(history=-1)
    parser.parse(data.encode("ascii"))
    return parser.history(), parser.events()


def fuzz_case(string: str, suffix: str | None = None) -> list[str]:
    return list(
        set(
            map(
                lambda parts: "".join(parts) + suffix if suffix else "".join(parts),
                itertools.product(*zip(string.upper(), string.lower())),
            )
        )
    )


class TestParserBasic:
    @pytest.mark.parametrize("data", fuzz_case("ping", "\r\n"))
    def test_parse_ping(self, data: str):
        history, events = parse_text(data)
        assert history == [
            State.OP_START,
            State.OP_P,
            State.OP_PI,
            State.OP_PIN,
            State.OP_PING,
            State.OP_END,
            State.OP_START,
        ]
        assert events == [
            Event(operation=Operation.PING),
        ]

    @pytest.mark.parametrize("data", fuzz_case("pong", "\r\n"))
    def test_parse_pong(self, data: str):
        history, events = parse_text(data)
        assert history == [
            State.OP_START,
            State.OP_P,
            State.OP_PO,
            State.OP_PON,
            State.OP_PONG,
            State.OP_END,
            State.OP_START,
        ]
        assert events == [
            Event(operation=Operation.PONG),
        ]

    @pytest.mark.parametrize("data", fuzz_case("+ok", "\r\n"))
    def test_parse_ok(self, data: str):
        history, events = parse_text(data)
        assert history == [
            State.OP_START,
            State.OP_PLUS,
            State.OP_PLUS_O,
            State.OP_PLUS_OK,
            State.OP_END,
            State.OP_START,
        ]
        assert events == [
            Event(operation=Operation.OK),
        ]

    @pytest.mark.parametrize(
        "data", fuzz_case("-err", " this is the error message\r\n")
    )
    def test_parse_err(self, data: str):
        history, events = parse_text(data)
        assert history == [
            State.OP_START,
            State.OP_MINUS,
            State.OP_MINUS_E,
            State.OP_MINUS_ER,
            State.OP_MINUS_ERR,
            State.OP_MINUS_ERR_SPC,
            State.MINUS_ERR_ARG,
            State.OP_END,
            State.OP_START,
        ]
        assert events == [
            ErrorEvent(operation=Operation.ERR, message="this is the error message"),
        ]


class TestParserAdvanced:
    @pytest.mark.parametrize("data", fuzz_case("ping\r\npong\r\n"))
    def test_parse_ping_pong(self, data: str):
        history, events = parse_text(data)
        assert history == [
            State.OP_START,
            State.OP_P,
            State.OP_PI,
            State.OP_PIN,
            State.OP_PING,
            State.OP_END,
            State.OP_START,
            State.OP_P,
            State.OP_PO,
            State.OP_PON,
            State.OP_PONG,
            State.OP_END,
            State.OP_START,
        ]
        assert events == [
            Event(operation=Operation.PING),
            Event(operation=Operation.PONG),
        ]
