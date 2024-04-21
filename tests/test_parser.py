import pytest
from protocol.parser import Parser, State, Event, Operation


class TestParser:
    def parse(self, data: bytes) -> tuple[list[State], list[Event]]:
        parser = Parser(history=-1)
        parser.parse(data)
        return parser.history(), parser.events()

    def test_parse_ping(self):
        history, events = self.parse(b"PING\r\n")
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

    @pytest.mark.skip
    def test_parse_pong(self):
        history, events = self.parse(b"PONG\r\n")
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
