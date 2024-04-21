from protocol.parser import Parser, State


class TestParser:

    def parse(self, data: bytes) -> list[State]:
        parser = Parser()
        states: list[State] = [parser.state]
        for byte in data:
            parser.parse(byte)
            states.append(parser.state)
        return states

    def test_parse_ping(self):
        assert self.parse(b"PING\r\n") == [
            State.OP_START,
            State.OP_P,
            State.OP_PI,
            State.OP_PIN,
            State.OP_PING,
            State.OP_START,
        ]
