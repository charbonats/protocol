import pytest
import itertools
from protocol.parser import Parser, State, Event, Operation


def parse_text(data: str) -> tuple[list[State], list[Event]]:
    parser = Parser(history=-1)
    parser.parse(data.encode("ascii"))
    return parser.history(), parser.events()


def fuzz_case(string: str) -> list[str]:
    return list(
        set(
            map(
                "".join,
                itertools.product(*zip(string.upper(), string.lower())),
            )
        )
    )


class TestParserBasic:
    @pytest.mark.parametrize("data", fuzz_case("ping\r\n"))
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

    @pytest.mark.parametrize("data", fuzz_case("pong\r\n"))
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

    @pytest.mark.parametrize("data", fuzz_case("+ok\r\n"))
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
