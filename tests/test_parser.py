import pytest
import itertools
from protocol.parser import Parser, State, Event, Operation


def combinations(string: str, suffix: str) -> list[str]:
    return map(
        lambda values: "".join(values) + suffix,
        itertools.product(*zip(string.upper(), string.lower())),
    )


class TestParser:
    def parse(self, data: bytes) -> tuple[list[State], list[Event]]:
        parser = Parser(history=-1)
        parser.parse(data)
        return parser.history(), parser.events()

    @pytest.mark.parametrize("data", combinations("ping", "\r\n"))
    def test_parse_ping(self, data: str):
        history, events = self.parse(data.encode("ascii"))
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

    @pytest.mark.parametrize("data", combinations("pong", "\r\n"))
    def test_parse_pong(self, data: str):
        history, events = self.parse(data.encode())
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
