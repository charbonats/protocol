from __future__ import annotations

import json
import sys

import pytest
from protocol import Backend, make_parser
from protocol.common import (
    OK_EVENT,
    PING_EVENT,
    PONG_EVENT,
    ErrorEvent,
    HMsgEvent,
    InfoEvent,
    MsgEvent,
    ParserClosedError,
    ProtocolError,
    Version,
)


def make_server_info(
    server_id: str = "test",
    server_name: str = "test",
    version: str = "0.0.0-test",
    go: str = "go0.0.0-test",
    host: str = "memory",
    port: int = 0,
    headers: bool = True,
    max_payload: int = 1024 * 1024,
    proto: int = 1,
    auth_required: bool | None = None,
    tls_required: bool | None = None,
    tls_verify: bool | None = None,
    tls_available: bool | None = None,
    connect_urls: list[str] | None = None,
    ws_connect_urls: list[str] | None = None,
    ldm: bool | None = None,
    git_commit: str | None = None,
    jetstream: bool | None = None,
    ip: str | None = None,
    client_ip: str | None = None,
    nonce: str | None = None,
    cluster: str | None = None,
    domain: str | None = None,
    xkey: str | None = None,
) -> str:
    info_dict: dict[str, object] = {
        "server_id": server_id,
        "server_name": server_name,
        "version": version,
        "go": go,
        "host": host,
        "port": port,
        "headers": headers,
        "max_payload": max_payload,
        "proto": proto,
    }
    if auth_required is not None:
        info_dict["auth_required"] = auth_required
    if tls_required is not None:
        info_dict["tls_required"] = tls_required
    if tls_verify is not None:
        info_dict["tls_verify"] = tls_verify
    if tls_available is not None:
        info_dict["tls_available"] = tls_available
    if connect_urls is not None:
        info_dict["connect_urls"] = connect_urls
    if ws_connect_urls is not None:
        info_dict["ws_connect_urls"] = ws_connect_urls
    if ldm is not None:
        info_dict["ldm"] = ldm
    if git_commit is not None:
        info_dict["git_commit"] = git_commit
    if jetstream is not None:
        info_dict["jetstream"] = jetstream
    if ip is not None:
        info_dict["ip"] = ip
    if client_ip is not None:
        info_dict["client_ip"] = client_ip
    if nonce is not None:
        info_dict["nonce"] = nonce
    if cluster is not None:
        info_dict["cluster"] = cluster
    if domain is not None:
        info_dict["domain"] = domain
    if xkey is not None:
        info_dict["xkey"] = xkey
    json_info = json.dumps(info_dict, separators=(",", ":"), sort_keys=True)
    return f"INFO {json_info}\r\n"


@pytest.mark.parametrize(
    "backend",
    [Backend.PARSER_300, Backend.PARSER_310, Backend.PARSER_RE],
)
class TestParserBasic:
    def skip_if(self, backend: str, reason: str) -> None:
        if self.backend == backend:
            pytest.skip(reason)

    @pytest.fixture(autouse=True)
    def setup(self, backend: Backend) -> None:
        self.backend = backend
        if sys.version_info < (3, 10) and backend == Backend.PARSER_310:
            pytest.skip("Parser 3.10 is not available in this Python version")
        self.parser = make_parser(backend)

    @pytest.mark.parametrize(
        "data",
        [
            [b"PING\r\n"],
            [b"PING\r", b"\n"],
            [b"PING", b"\r\n"],
            [b"PING", b"\r", b"\n"],
            [b"PIN", b"G\r\n"],
            [b"P", b"ING\r\n"],
            [b"P", b"I", b"N", b"G", b"\r", b"\n"],
        ],
    )
    def test_parse_ping(self, data: list[bytes]):
        for chunk in data:
            self.parser.parse(chunk)
        assert self.parser.events_received() == [
            PING_EVENT,
        ]

    @pytest.mark.parametrize(
        "data",
        [
            [b"PONG\r\n"],
            [b"PONG\r", b"\n"],
            [b"PONG", b"\r\n"],
            [b"PONG", b"\r", b"\n"],
            [b"PON", b"G\r\n"],
            [b"P", b"ONG\r\n"],
            [b"P", b"O", b"N", b"G", b"\r", b"\n"],
        ],
    )
    def test_parse_pong(self, data: list[bytes]):
        for chunk in data:
            self.parser.parse(chunk)
        assert self.parser.events_received() == [
            PONG_EVENT,
        ]

    @pytest.mark.parametrize(
        "data",
        [
            [b"+OK\r\n"],
            [b"+OK\r", b"\n"],
            [b"+OK", b"\r\n"],
            [b"+OK", b"\r", b"\n"],
            [b"+O", b"K\r\n"],
            [b"+", b"OK\r\n"],
            [b"+", b"O", b"K", b"\r", b"\n"],
        ],
    )
    def test_parse_ok(self, data: list[bytes]):
        for chunk in data:
            self.parser.parse(chunk)
        assert self.parser.events_received() == [
            OK_EVENT,
        ]

    @pytest.mark.parametrize(
        "data",
        [
            [b"-ERR 'This is the error message'\r\n"],
            [b"-ERR 'This is the error message'\r", b"\n"],
            [b"-ERR 'This is the error message'", b"\r\n"],
            [b"-ERR 'This is the error message'", b"\r", b"\n"],
            [b"-ERR 'This is the error", b" message'\r\n"],
            [b"-ERR 'This is the", b" error message'\r\n"],
            [b"-ERR 'This is the", b" error message'", b"\r", b"\n"],
            [b"-", b"ERR 'This is the error message'\r\n"],
            [b"-ERR", b" 'This is the error message'\r\n"],
        ],
    )
    def test_parse_err(self, data: list[bytes]):
        for chunk in data:
            self.parser.parse(chunk)
        assert self.parser.events_received() == [
            ErrorEvent(message="this is the error message"),
        ]

    @pytest.mark.parametrize(
        "data",
        [
            [b"MSG the.subject 1234 0\r\n\r\n"],
            [b"MSG the.subject 1234 0", b"\r\n", b"\r\n"],
            [b"MSG the.subject 1234 0\r", b"\n", b"\r\n"],
            [b"MSG the.subject 1234 0", b"\r", b"\n", b"\r\n"],
            [b"MSG the.subject 1234", b" 0\r\n\r\n"],
            [b"MSG the.subject", b" 1234 0\r\n\r\n"],
            [b"MSG ", b"the.subject", b" 1234 0\r\n\r\n"],
            [b"M", b"SG ", b"the.subject", b" 1234 0\r\n\r\n"],
        ],
    )
    def test_parse_msg_with_empty_payload(self, data: list[bytes]):
        for chunk in data:
            self.parser.parse(chunk)
        assert self.parser.events_received() == [
            MsgEvent(
                sid=1234,
                subject="the.subject",
                reply_to="",
                payload=bytearray(),
            ),
        ]

    @pytest.mark.parametrize(
        "data",
        [
            [b"MSG the.subject 1234 the.reply.subject 0\r\n\r\n"],
            [b"MSG the.subject 1234 the.reply.subject 0", b"\r\n", b"\r\n"],
            [b"MSG the.subject 1234 the.reply.subject 0\r", b"\n", b"\r\n"],
            [b"MSG the.subject 1234 the.reply.subject 0", b"\r", b"\n", b"\r\n"],
            [b"MSG the.subject 1234 the.reply.subject", b" 0\r\n\r\n"],
            [b"MSG the.subject 1234 ", b"the.reply.subject", b" 0\r\n\r\n"],
            [b"MSG the.subject", b" 1234 ", b"the.reply.subject", b" 0\r\n\r\n"],
            [b"MSG", b" the.subject", b" 1234 ", b"the.reply.subject", b" 0\r\n\r\n"],
            [
                b"M",
                b"SG",
                b" the.subject",
                b" 1234 ",
                b"the.reply.subject",
                b" 0\r\n\r\n",
            ],
        ],
    )
    def test_parse_msg_with_reply_and_empty_payload(self, data: list[bytes]):
        for chunk in data:
            self.parser.parse(chunk)
        assert self.parser.events_received() == [
            MsgEvent(
                sid=1234,
                subject="the.subject",
                reply_to="the.reply.subject",
                payload=bytearray(),
            ),
        ]

    @pytest.mark.parametrize(
        "data",
        [
            [b"MSG the.subject 1234 12\r\nhello world!\r\n"],
            [b"MSG the.subject 1234 12", b"\r\n", b"hello world!\r\n"],
            [b"MSG the.subject 1234 12\r", b"\n", b"hello world!\r\n"],
            [b"MSG the.subject 1234 12", b"\r", b"\n", b"hello ", b"world!\r", b"\n"],
            [
                b"M",
                b"SG the",
                b".subject 12",
                b"34 12",
                b"\r",
                b"\n",
                b"hello ",
                b"world!\r\n",
            ],
        ],
    )
    def test_parse_msg(self, data: list[bytes]):
        for chunk in data:
            self.parser.parse(chunk)
        assert self.parser.events_received() == [
            MsgEvent(
                sid=1234,
                subject="the.subject",
                reply_to="",
                payload=bytearray(b"hello world!"),
            ),
        ]

    @pytest.mark.parametrize(
        "data",
        [
            [b"MSG the.subject 1234 the.reply.subject 12\r\nhello world!\r\n"],
            [b"MSG", b" the.subject 1234 the.reply.subject 12\r\nhello world!\r\n"],
            [
                b"MSG",
                b" the.",
                b"subject 1234 the.reply.subject 12\r\nhello world!\r\n",
            ],
            [
                b"MSG",
                b" the.",
                b"subject ",
                b"1234 the.reply.subject 12\r\nhello world!\r\n",
            ],
            [
                b"MSG",
                b" the.",
                b"subject ",
                b"1234",
                b" the.reply.subject 12\r\nhello world!\r\n",
            ],
            [
                b"MSG",
                b" the.",
                b"subject ",
                b"1234",
                b" the.reply.subject ",
                b"12\r\nhello world!\r\n",
            ],
            [
                b"M",
                b"SG",
                b" the.",
                b"subject ",
                b"1234",
                b" the.reply.subject ",
                b"12\r\nhello world!\r\n",
            ],
        ],
    )
    def test_parse_msg_with_reply(self, data: list[bytes]):
        for chunk in data:
            self.parser.parse(chunk)
        assert self.parser.events_received() == [
            MsgEvent(
                sid=1234,
                subject="the.subject",
                reply_to="the.reply.subject",
                payload=bytearray(b"hello world!"),
            ),
        ]

    @pytest.mark.parametrize(
        "data",
        [
            [b"HMSG the.subject 1234 4 4\r\n\r\n\r\n\r\n"],
            [b"HMSG the.subject 1234 4 4\r\n", b"\r\n\r\n\r\n"],
            [b"HMSG the.subject 1234 4 4\r\n\r\n", b"\r\n", b"\r\n"],
            [b"HMSG the.subject 1234 4 4\r\n\r\n", b"\r", b"\n", b"\r\n"],
            [b"HMSG the.subject 1234 4", b" 4\r\n\r\n", b"\r\n", b"\r\n"],
            [b"HMSG the.subject 1234 ", b"4", b" 4\r\n\r\n", b"\r\n", b"\r\n"],
            [b"HMSG the.subject", b" 1234 ", b"4", b" 4\r\n\r\n", b"\r\n", b"\r\n"],
            [
                b"HMSG",
                b" the.subject",
                b" 1234 ",
                b"4",
                b" 4\r\n\r\n",
                b"\r\n",
                b"\r\n",
            ],
            [
                b"H",
                b"MSG",
                b" the.subject",
                b" 1234 ",
                b"4",
                b" 4\r\n\r\n",
                b"\r\n",
                b"\r\n",
            ],
        ],
    )
    def test_parse_hmsg_with_empty_header_and_empty_payload(self, data: list[bytes]):
        for chunk in data:
            self.parser.parse(chunk)
        assert self.parser.events_received() == [
            HMsgEvent(
                sid=1234,
                subject="the.subject",
                reply_to="",
                payload=bytearray(),
                header=bytearray(),
            ),
        ]

    @pytest.mark.parametrize(
        "data",
        [
            [b"HMSG the.subject 1234 22 22\r\nNATS/1.0\r\nFoo: Bar\r\n\r\n\r\n"],
            [b"HMSG the.subject 1234 22 22\r\nNATS/1.0\r\nFoo: Bar\r\n\r\n", b"\r\n"],
            [b"HMSG the.subject 1234 22 22\r\nNATS/1.0\r\nFoo: Bar\r\n", b"\r\n\r\n"],
            [
                b"HMSG the.subject 1234 22 22\r\nNATS/1.0\r\nFoo: Bar\r\n",
                b"\r",
                b"\n",
                b"\r",
                b"\n",
            ],
            [
                b"HMSG the.subject 1234 22",
                b" 22\r\nNATS/1.0\r\nFoo: Bar\r\n\r\n",
                b"\r\n",
            ],
            [
                b"HMSG the.subject 1234",
                b" 22 22\r\nNATS/1.0\r\nFoo: Bar\r\n\r\n",
                b"\r\n",
            ],
            [
                b"HMSG the.subject",
                b" 1234 22 22\r\nNATS/1.0\r\nFoo: Bar\r\n\r\n",
                b"\r\n",
            ],
            [
                b"HMSG",
                b" the.subject 1234 22 22\r\nNATS/1.0\r\nFoo: Bar\r\n\r\n",
                b"\r\n",
            ],
            [
                b"H",
                b"MSG",
                b" the.subject ",
                b"1234 22 22\r\nNATS/1.0\r\nFoo: Bar\r\n\r\n",
                b"\r\n",
            ],
        ],
    )
    def test_parse_hmsg_with_header_and_empty_payload(self, data: list[bytes]):
        for chunk in data:
            self.parser.parse(chunk)
        assert self.parser.events_received() == [
            HMsgEvent(
                sid=1234,
                subject="the.subject",
                reply_to="",
                payload=bytearray(),
                header=bytearray(b"NATS/1.0\r\nFoo: Bar"),
            ),
        ]

    @pytest.mark.parametrize(
        "data",
        [
            [
                b"HMSG the.subject 1234 18 30\r\nNATS/1.0\r\nA: B\r\n\r\nhello world!\r\n",
            ],
            [
                b"HMSG the.subject 1234 18 30\r\nNATS/1.0\r\nA: B\r\n\r\n",
                b"hello world!\r\n",
            ],
            [
                b"HMSG the.subject 1234 18 30\r\nNATS/1.0\r\nA: B\r\n",
                b"\r\nhello world!\r\n",
            ],
            [
                b"HMSG the.subject 1234 18 30\r\nNATS/1.0\r\nA: B\r",
                b"\n",
                b"\r",
                b"\nhello world!\r\n",
            ],
            [
                b"HMSG the.subject 1234 18",
                b" 30\r\nNATS/1.0\r\nA: B\r\n\r\n",
                b"hello world!\r\n",
            ],
            [
                b"HMSG the.subject 1234",
                b" 18 30\r\nNATS/1.0\r\nA: B\r\n\r\n",
                b"hello world!\r\n",
            ],
            [
                b"HMSG the.subject",
                b" 1234 1",
                b"8 30\r\nNATS/1.0\r\nA: B\r\n\r\n",
                b"hello world!\r\n",
            ],
            [
                b"H",
                b"MSG",
                b" the.subject 1",
                b"234 18 3",
                b"0\r\nNATS/1.0\r\nA: B\r\n\r\n",
                b"hello world!\r\n",
            ],
        ],
    )
    def test_parse_hmsg(self, data: list[bytes]):
        for chunk in data:
            self.parser.parse(chunk)
        assert self.parser.events_received() == [
            HMsgEvent(
                sid=1234,
                subject="the.subject",
                reply_to="",
                payload=bytearray(b"hello world!"),
                header=bytearray(b"NATS/1.0\r\nA: B"),
            ),
        ]

    @pytest.mark.parametrize(
        "data",
        [
            [
                b"HMSG the.subject 1234 the.reply.subject 18 30\r\nNATS/1.0\r\nA: B\r\n\r\nhello world!\r\n"
            ],
            [
                b"HMSG the.subject 1234 the.reply.subject 18 30\r\nNATS/1.0\r\nA: B\r\n\r\n",
                b"hello world!\r\n",
            ],
            [
                b"HMSG the.subject 1234 the.reply.subject 18 30\r\nNATS/1.0\r\nA: B\r\n",
                b"\r\nhello world!\r\n",
            ],
            [
                b"HMSG the.subject 1234 the.reply.subject 18 30\r\nNATS/1.0\r\nA: B\r",
                b"\n",
                b"\r",
                b"\nhello world!\r\n",
            ],
            [
                b"HMSG the.subject 1234 the.reply.subject 1",
                b"8",
                b" 3",
                b"0\r\nNATS/1.0\r\nA: B\r\n\r\n",
                b"hello world!\r\n",
            ],
            [
                b"HMSG the.subject 1234 the.reply.subject",
                b" 18 30\r\nNATS/1.0\r\nA: B\r\n\r\n",
                b"hello world!\r\n",
            ],
            [
                b"H",
                b"M",
                b"SG the.subject",
                b" 1234 the.reply.s",
                b"ubject 18 30\r\nNATS/1.0\r\nA: B\r\n\r\n",
                b"hello world!\r\n",
            ],
        ],
    )
    def test_parse_hmsg_with_reply(self, data: list[bytes]):
        for chunk in data:
            self.parser.parse(chunk)
        assert self.parser.events_received() == [
            HMsgEvent(
                sid=1234,
                subject="the.subject",
                reply_to="the.reply.subject",
                payload=bytearray(b"hello world!"),
                header=bytearray(b"NATS/1.0\r\nA: B"),
            ),
        ]

    @pytest.mark.parametrize(
        "data",
        [[make_server_info().encode()]],
    )
    def test_parse_info(self, data: list[bytes]):
        for chunk in data:
            self.parser.parse(chunk)
        assert self.parser.events_received() == [
            InfoEvent(
                proto=1,
                server_id="test",
                server_name="test",
                version=Version(major=0, minor=0, patch=0, dev="test"),
                go="go0.0.0-test",
                host="memory",
                port=0,
                max_payload=1048576,
                headers=True,
                client_id=None,
                auth_required=None,
                tls_required=None,
                tls_verify=None,
                tls_available=None,
                connect_urls=None,
                ws_connect_urls=None,
                ldm=None,
                git_commit=None,
                jetstream=None,
                ip=None,
                client_ip=None,
                nonce=None,
                cluster=None,
                domain=None,
                xkey=None,
            ),
        ]

    @pytest.mark.parametrize(
        "data",
        [
            [b"PING\r\n", b"PONG\r\n"],
            [b"PING\r\nPONG\r\n"],
            [b"PING\r\nPONG", b"\r\n"],
            [b"PING", b"\r\nPONG", b"\r\n"],
            [b"P", b"ING", b"\r\nPONG", b"\r\n"],
            [b"P", b"ING", b"\r\nP", b"ONG", b"\r\n"],
        ],
    )
    def test_parse_ping_pong(self, data: list[bytes]):
        for chunk in data:
            self.parser.parse(chunk)
        assert self.parser.events_received() == [
            PING_EVENT,
            PONG_EVENT,
        ]

    @pytest.mark.parametrize(
        "data",
        [
            [b"PING\r\n", b"+OK\r\n"],
            [b"PING\r\n+OK\r\n"],
            [b"PING\r\n+", b"OK\r\n"],
            [b"PING\r", b"\n+", b"OK\r\n"],
        ],
    )
    def test_parse_ping_ok(self, data: list[bytes]):
        for chunk in data:
            self.parser.parse(chunk)
        assert self.parser.events_received() == [PING_EVENT, OK_EVENT]

    @pytest.mark.parametrize(
        "data",
        [
            [b"-ERR 'the error message'\r\n", b"-ERR 'the other error message'\r\n"],
            [b"-ERR 'the error message'\r\n-ERR 'the other error message'\r\n"],
        ],
    )
    def test_parse_err_err(self, data: list[bytes]):
        for chunk in data:
            self.parser.parse(chunk)
        assert self.parser.events_received() == [
            ErrorEvent(message="the error message"),
            ErrorEvent(message="the other error message"),
        ]

    @pytest.mark.parametrize("data", [[b"invalid\r\n"]])
    def test_error_invalid_string(self, data: list[bytes]):
        with pytest.raises(ProtocolError) as exc:
            for chunk in data:
                self.parser.parse(chunk)
        assert exc.match("nats: protocol error")

    @pytest.mark.parametrize("data", [[b"PONGG\r\n"]])
    def test_error_invalid_pongg(self, data: list[bytes]):
        with pytest.raises(ProtocolError) as exc:
            for chunk in data:
                self.parser.parse(chunk)
        assert exc.match("nats: protocol error")

    @pytest.mark.parametrize("data", [[b"PINGG\r\n"]])
    def test_error_invalid_pingg(self, data: list[bytes]):
        with pytest.raises(ProtocolError) as exc:
            for chunk in data:
                self.parser.parse(chunk)
        assert exc.match("nats: protocol error")

    @pytest.mark.parametrize("data", [[b"+OKK\r\n"]])
    def test_error_invalid_okk(self, data: list[bytes]):
        with pytest.raises(ProtocolError) as exc:
            for chunk in data:
                self.parser.parse(chunk)
        assert exc.match("nats: protocol error")

    @pytest.mark.parametrize("data", [[b"-ERRR 'the error message'\r\n"]])
    def test_error_invalid_errr(self, data: list[bytes]):
        with pytest.raises(ProtocolError) as exc:
            for chunk in data:
                self.parser.parse(chunk)
        assert exc.match("nats: protocol error")

    @pytest.mark.parametrize(
        "data",
        [
            [b"-ERR the error message\r\n"],
            [b"-ERR 'the error message\r\n"],
            [b"-ERR the error message'\r\n"],
        ],
    )
    def test_error_invalid_err_without_quote(self, data: list[bytes]):
        with pytest.raises(ProtocolError) as exc:
            for chunk in data:
                self.parser.parse(chunk)
        assert exc.match("nats: protocol error")

    @pytest.mark.parametrize("data", [[b"MSGG the.subject 1234 0\r\n\r\n"]])
    def test_error_invalid_msgg(self, data: list[bytes]):
        with pytest.raises(ProtocolError) as exc:
            for chunk in data:
                self.parser.parse(chunk)
        assert exc.match("nats: protocol error")

    @pytest.mark.parametrize("data", [[b"MSG\r\n"]])
    def test_error_invalid_msg_without_arg(self, data: list[bytes]):
        with pytest.raises(ProtocolError) as exc:
            for chunk in data:
                self.parser.parse(chunk)
        assert exc.match("nats: protocol error")

    @pytest.mark.parametrize("data", [[b"MSG \r\n"]])
    def test_error_invalid_msg_with_empty_arg(self, data: list[bytes]):
        with pytest.raises(ProtocolError) as exc:
            for chunk in data:
                self.parser.parse(chunk)
        assert exc.match("nats: protocol error")

    @pytest.mark.parametrize("data", [[b"HMSG\r\n"]])
    def test_error_invalid_hmsg_without_arg(self, data: list[bytes]):
        with pytest.raises(ProtocolError) as exc:
            for chunk in data:
                self.parser.parse(chunk)
        assert exc.match("nats: protocol error")

    @pytest.mark.parametrize("data", [[b"HMSG \r\n"]])
    def test_error_invalid_hmsg_with_empty_arg(self, data: list[bytes]):
        with pytest.raises(ProtocolError) as exc:
            for chunk in data:
                self.parser.parse(chunk)
        assert exc.match("nats: protocol error")

    @pytest.mark.parametrize("data", [[b"MSG the.subject 1234a 0\r\n\r\n"]])
    def test_error_invalid_msg_sid(self, data: list[bytes]):
        with pytest.raises(ProtocolError) as exc:
            for chunk in data:
                self.parser.parse(chunk)
        assert exc.match("nats: protocol error")

    @pytest.mark.parametrize("data", [[b"MSG the subject 1234 0\r\n\r\n"]])
    def test_error_invalid_msg_subject_with_space(self, data: list[bytes]):
        with pytest.raises(ProtocolError) as exc:
            for chunk in data:
                self.parser.parse(chunk)
        assert exc.match("nats: protocol error")

    @pytest.mark.parametrize(
        "data", [[b"MSG the.subject 1234 the reply.subject 0\r\n\r\n"]]
    )
    def test_error_invalid_msg_reply_subject_with_space(self, data: list[bytes]):
        with pytest.raises(ProtocolError) as exc:
            for chunk in data:
                self.parser.parse(chunk)
        assert exc.match("nats: protocol error")

    @pytest.mark.parametrize("data", [[b"MSG the.subject 1234 0a\r\n\r\n"]])
    def test_error_invalid_msg_size(self, data: list[bytes]):
        with pytest.raises(ProtocolError) as exc:
            for chunk in data:
                self.parser.parse(chunk)
        assert exc.match("nats: protocol error")

    @pytest.mark.parametrize(
        "data",
        [
            [b"HMSGG the.subject 1234 0 0\r\n\r\n\r\n"],
            [b"HMSGG the.subjec", b"t 1234 0 0\r\n\r\n\r\n"],
        ],
    )
    def test_error_invalid_hmsgg(self, data: list[bytes]):
        with pytest.raises(ProtocolError) as exc:
            for chunk in data:
                self.parser.parse(chunk)
        assert exc.match("nats: protocol error")

    @pytest.mark.parametrize(
        "data",
        [
            [b"HMSG the.subject 1234a 0 0\r\n\r\n\r\n"],
            [b"HMSG the.subject 123", b"4a 0 0\r\n\r\n\r\n"],
        ],
    )
    def test_error_invalid_hmsg_sid(self, data: list[bytes]):
        with pytest.raises(ProtocolError) as exc:
            for chunk in data:
                self.parser.parse(chunk)
        assert exc.match("nats: protocol error")

    @pytest.mark.parametrize(
        "data",
        [
            [b"HMSG the subject 1234 0 0\r\n\r\n\r\n"],
            [b"HMSG th", b"e subject 1234 0 0\r\n\r\n\r\n"],
        ],
    )
    def test_error_invalid_hmsg_subject_with_space(self, data: list[bytes]):
        with pytest.raises(ProtocolError) as exc:
            for chunk in data:
                self.parser.parse(chunk)
        assert exc.match("nats: protocol error")

    @pytest.mark.parametrize(
        "data",
        [
            [b"HMSG the.subject 1234 the reply.subject 0 0\r\n\r\n\r\n"],
            [b"HMS", b"G the.subject 1234 the reply.subject 0 0\r\n\r\n\r\n"],
        ],
    )
    def test_error_invalid_hmsg_reply_subject_with_space(self, data: list[bytes]):
        with pytest.raises(ProtocolError) as exc:
            for chunk in data:
                self.parser.parse(chunk)
        assert exc.match("nats: protocol error")

    @pytest.mark.parametrize(
        "data",
        [
            [b"HMSG the.subject 1234 0a 0\r\n\r\n\r\n"],
            [b"HMSG the.subject 1234 0", b"a 0\r\n\r\n\r\n"],
        ],
    )
    def test_error_invalid_hmsg_header_size(self, data: list[bytes]):
        with pytest.raises(ProtocolError) as exc:
            for chunk in data:
                self.parser.parse(chunk)
        assert exc.match("nats: protocol error")

    @pytest.mark.parametrize(
        "data",
        [
            [b"HMSG the.subject 1234 0 0a\r\n\r\n\r\n"],
            [b"HMSG the.subject 1234 0 ", b"0a\r\n\r\n\r\n"],
        ],
    )
    def test_error_invalid_hmsg_size(self, data: list[bytes]):
        with pytest.raises(ProtocolError) as exc:
            for chunk in data:
                self.parser.parse(chunk)
        assert exc.match("nats: protocol error")

    @pytest.mark.parametrize(
        "data",
        [
            [b"HMSG the.subject 1234 5 5\r\n10000\r\n"],
            [b"HMSG the.subject 1", b"234 5 5\r\n10000\r\n"],
        ],
    )
    def test_error_invalid_hmsg_error_end(self, data: list[bytes]):
        self.skip_if(
            Backend.PARSER_RE, "Parser RE does not check for invalid header end"
        )
        with pytest.raises(ProtocolError) as exc:
            for chunk in data:
                self.parser.parse(chunk)
        assert exc.match("nats: protocol error")

    @pytest.mark.parametrize(
        "data",
        [
            [b"HMSG the.subject 1234 4 4\r\n0000\r\n"],
            [b"HMSG", b" the.subject 1234 4 4\r\n0000\r\n"],
            [b"HMSG", b" the.subject 1234 4 4\r\n00", b"00\r\n"],
        ],
    )
    def test_error_invalid_empty_hmsg_error_end(self, data: list[bytes]):
        self.skip_if(
            Backend.PARSER_RE, "Parser RE does not check for invalid header end"
        )
        with pytest.raises(ProtocolError) as exc:
            for chunk in data:
                self.parser.parse(chunk)
        assert exc.match("nats: protocol error")

    @pytest.mark.parametrize(
        "letter",
        [
            "a",
            "b",
            "c",
            "d",
            "e",
            "f",
            "g",
            "h",
            "i",
            "j",
            "k",
            "l",
            "m",
            "n",
            "o",
            "p",
            "q",
            "r",
            "s",
            "t",
            "u",
            "v",
            "w",
            "x",
            "y",
            "z",
            "A",
            "B",
            "C",
            "D",
            "E",
            "F",
            "G",
            "J",
            "K",
            "L",
            "N",
            "O",
            "Q",
            "R",
            "S",
            "T",
            "U",
            "V",
            "W",
            "X",
            "Y",
            "Z",
            "0",
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "*",
            ">",
            "\t",
            " ",
            "\n",
            "\r",
            "{",
        ],
    )
    def test_error_invalid_start(self, letter: str):
        self.skip_if(Backend.PARSER_RE, "Parser RE does not check for invalid letters")
        with pytest.raises(ProtocolError) as exc:
            self.parser.parse(letter.encode())
        assert exc.match("nats: protocol error")

    @pytest.mark.parametrize("data", [[b"INFO\r\n"]])
    def test_error_invalid_info(self, data: list[bytes]):
        with pytest.raises(ProtocolError) as exc:
            for chunk in data:
                self.parser.parse(chunk)
        assert exc.match("nats: protocol error")

    @pytest.mark.parametrize("data", [[b"INFO \r\n"]])
    def test_error_invalid_info_without_arg(self, data: list[bytes]):
        with pytest.raises(ProtocolError) as exc:
            for chunk in data:
                self.parser.parse(chunk)
        assert exc.match("nats: protocol error")

    @pytest.mark.parametrize("data", [[b"INFO  \r\n"], [b"INFO ", b" \r\n"]])
    def test_error_invalid_info_with_empty_arg(self, data: list[bytes]):
        with pytest.raises(ProtocolError) as exc:
            for chunk in data:
                self.parser.parse(chunk)
        assert exc.match("nats: protocol error")

    def test_close_parser(self) -> None:
        self.parser.parse(b"+OK\r\n")
        assert self.parser.events_received() == [OK_EVENT]
        self.parser.close()
        with pytest.raises(ParserClosedError) as exc:
            self.parser.parse(b"+OK\r\n")
        assert exc.match("nats: parser closed")


class TestParserRepr:
    def test_parser_300_repr(self) -> None:
        parser = make_parser(Backend.PARSER_300)
        assert repr(parser) == "<nats protocol parser backend=300>"

    def test_parser_310_repr(self) -> None:
        if sys.version_info < (3, 10):
            pytest.skip("python 3.10 or later is required")
        parser = make_parser(Backend.PARSER_310)
        assert repr(parser) == "<nats protocol parser backend=310>"

    def test_parser_re_repr(self) -> None:
        parser = make_parser(Backend.PARSER_RE)
        assert repr(parser) == "<nats protocol parser backend=re>"
