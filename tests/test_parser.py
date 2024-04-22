import itertools

import pytest
from protocol.parser import ErrorEvent, Event, MsgEvent, Operation, Parser, State


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

    @pytest.mark.parametrize(
        "data", fuzz_case("msg", " the.subject 1234 12\r\nhello world!\r\n")
    )
    def test_parse_msg(self, data: str):
        history, events = parse_text(data)
        assert history == [
            State.OP_START,
            State.OP_M,
            State.OP_MS,
            State.OP_MSG,
            State.OP_MSG_SPC,
            State.MSG_ARG,
            State.MSG_END,
            State.MSG_PAYLOAD,
            State.OP_END,
            State.OP_START,
        ]
        assert events == [
            MsgEvent(
                operation=Operation.MSG,
                sid=1234,
                subject="the.subject",
                reply_to="",
                payload_size=12,
                payload=b"hello world!",
            ),
        ]

    @pytest.mark.parametrize(
        "data",
        fuzz_case("msg", " the.subject 1234 the.reply.subject 12\r\nhello world!\r\n"),
    )
    def test_parse_msg_with_reply(self, data: str):
        history, events = parse_text(data)
        assert history == [
            State.OP_START,
            State.OP_M,
            State.OP_MS,
            State.OP_MSG,
            State.OP_MSG_SPC,
            State.MSG_ARG,
            State.MSG_END,
            State.MSG_PAYLOAD,
            State.OP_END,
            State.OP_START,
        ]
        assert events == [
            MsgEvent(
                operation=Operation.MSG,
                sid=1234,
                subject="the.subject",
                reply_to="the.reply.subject",
                payload_size=12,
                payload=b"hello world!",
            ),
        ]


class TestParserAdvanced:
    @pytest.mark.parametrize("data", ["ping\r\npong\r\n"])
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

    @pytest.mark.parametrize("data", ["ping\r\n+ok\r\n"])
    def test_parse_ping_ok(self, data: str):
        history, events = parse_text(data)
        assert history == [
            State.OP_START,
            State.OP_P,
            State.OP_PI,
            State.OP_PIN,
            State.OP_PING,
            State.OP_END,
            State.OP_START,
            State.OP_PLUS,
            State.OP_PLUS_O,
            State.OP_PLUS_OK,
            State.OP_END,
            State.OP_START,
        ]
        assert events == [
            Event(operation=Operation.PING),
            Event(operation=Operation.OK),
        ]

    @pytest.mark.parametrize(
        "data", ["-err the error message\r\n-err the other error message\r\n"]
    )
    def test_parse_err_err(self, data: str):
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
            ErrorEvent(operation=Operation.ERR, message="the error message"),
            ErrorEvent(operation=Operation.ERR, message="the other error message"),
        ]

    @pytest.mark.parametrize(
        "chunks",
        [
            [
                b"msg the.subject 1234 12\r\n",
                b"hello world!\r\n",
            ],
            [
                b"msg the.subject 1234 12\r\nhello",
                b" world!\r\n",
            ],
            [
                b"msg the.subject 1234 12\r\nhello",
                b" world!",
                b"\r\n",
            ],
            [
                b"msg the.subject",
                b" 1234 12\r\nhello world!\r\n",
            ],
            [
                b"msg the.subject",
                b" 1234 12\r\nhello world",
                b"!\r\n",
            ],
        ],
        ids=[
            "args_then_payload",
            "args_then_payload_in_chunks",
            "args_then_payload_in_chunks_then_cr",
            "chunked_args_then_payload",
            "chunked_args_then_chunked_payload",
        ],
    )
    def test_parse_msg_in_several_chunks(self, chunks: list[bytes]):
        parser = Parser(history=-1)
        for chunk in chunks:
            parser.parse(chunk)
        history, events = parser.history(), parser.events()
        assert history == [
            State.OP_START,
            State.OP_M,
            State.OP_MS,
            State.OP_MSG,
            State.OP_MSG_SPC,
            State.MSG_ARG,
            State.MSG_END,
            State.MSG_PAYLOAD,
            State.OP_END,
            State.OP_START,
        ]
        assert events == [
            MsgEvent(
                operation=Operation.MSG,
                sid=1234,
                subject="the.subject",
                reply_to="",
                payload_size=12,
                payload=b"hello world!",
            ),
        ]

    @pytest.mark.parametrize(
        "chunks",
        [
            [
                b"msg the.subject 1234 the.reply.subject 12\r\n",
                b"hello world!\r\n",
            ],
            [
                b"msg the.subject 1234 the.reply.subject 12\r\nhello",
                b" world!\r\n",
            ],
            [
                b"msg the.subject 1234 the.reply.subject 12\r\nhello",
                b" world!",
                b"\r\n",
            ],
            [
                b"msg the.subject",
                b" 1234 the.reply.subject 12\r\nhello world!\r\n",
            ],
            [
                b"msg the.subject 1234 the.reply.",
                b"subject 12\r\nhello world",
                b"!\r\n",
            ],
        ],
        ids=[
            "args_then_payload",
            "args_then_payload_in_chunks",
            "args_then_payload_in_chunks_then_cr",
            "chunked_args_then_payload",
            "chunked_args_then_chunked_payload",
        ],
    )
    def test_parse_msg_with_reply_in_several_chunks(self, chunks: list[bytes]):
        parser = Parser(history=-1)
        for chunk in chunks:
            parser.parse(chunk)
        history, events = parser.history(), parser.events()
        assert history == [
            State.OP_START,
            State.OP_M,
            State.OP_MS,
            State.OP_MSG,
            State.OP_MSG_SPC,
            State.MSG_ARG,
            State.MSG_END,
            State.MSG_PAYLOAD,
            State.OP_END,
            State.OP_START,
        ]
        assert events == [
            MsgEvent(
                operation=Operation.MSG,
                sid=1234,
                subject="the.subject",
                reply_to="the.reply.subject",
                payload_size=12,
                payload=b"hello world!",
            ),
        ]
